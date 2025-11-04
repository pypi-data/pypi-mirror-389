import asyncio
import json
import logging
from typing import Dict, List, Any
import json5
import httpx
from bs4 import BeautifulSoup

from .schema import HTTPRequest, HTTPResponse

logger = logging.getLogger("httpchain")


class RequestExecutor:

    @classmethod
    def _extract_meta_tags(cls, soup: BeautifulSoup) -> Dict[str, str]:
        meta_data = {}
        for meta_tag in soup.find_all('meta'):
            if 'content' not in meta_tag.attrs: continue
            key = meta_tag.attrs.get('property') or meta_tag.attrs.get('name')
            if key:
                meta_data[key] = meta_tag.attrs['content']
        return meta_data

    @classmethod
    def _parse_json_like_string(cls, text: str) -> Dict[str, Any]:
        """
        Robustly parses a string that could be standard JSON or JSONC.
        Tries standard `json` first for performance, falls back to `json5`.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug("Standard JSON parse failed. Falling back to json5 parser.")
            try:
                return json5.loads(text)
            except Exception: # Broad exception for any json5 parsing failure
                logger.warning("Failed to parse script content with both standard json and json5.")



    @classmethod
    def _extract_json_ld(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Finds all application/ld+json script tags and robustly parses their content.
        """
        json_ld_data = []
        script_tags = soup.find_all('script', type='application/ld+json')
        for tag in script_tags:
            if tag.string:
                parsed_data = cls._parse_json_like_string(tag.string)
                if parsed_data:
                    json_ld_data.append(parsed_data)
        return json_ld_data

    @classmethod
    def _extract_application_json(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Finds all application/json script tags and robustly parses their content.

        Args:
            soup (BeautifulSoup): The parsed HTML content.

        Returns:
            List[Dict[str, Any]]: A list of parsed JSON data from application/json script tags.
        """
        application_json_data = []
        script_tags = soup.find_all('script', type='application/json')

        for tag in script_tags:
            if tag.string:
                content = tag.string.strip()
                if content.startswith('<!--') and content.endswith('-->'):
                    content = content[4:-3].strip()
                parsed_data = cls._parse_json_like_string(content)
                if parsed_data:
                    application_json_data.append(parsed_data)

        return application_json_data

    @classmethod
    async def execute(cls, request: HTTPRequest) -> HTTPResponse:
        last_exception = None

        for attempt in range(request.request_retries + 1):
            try:
                request_kwargs = {
                    "method": request.request_method,
                    "url": request.request_url,
                    "headers": request.request_headers,
                    "params": request.request_params,
                    "cookies": request.request_cookies,
                    "json": request.request_json,
                    "data": request.request_data
                }
                final_kwargs = {k: v for k, v in request_kwargs.items() if v is not None}

                logger.info(
                    f"Attempt {attempt + 1}/{request.request_retries + 1}: "
                    f"Requesting {request.request_method} {request.request_url}"
                )
                logger.debug(f"Request kwargs: {final_kwargs}")

                async with httpx.AsyncClient(
                        verify=False, follow_redirects=request.request_follow_redirects,
                        timeout=httpx.Timeout(
                            timeout=request.request_connect_timeout + request.request_read_timeout,
                            connect=request.request_connect_timeout,
                            read=request.request_read_timeout
                        ),
                ) as client:
                    response = await client.request(**final_kwargs)

                failed = False
                failure_reason = None
                if 400 <= response.status_code <= 599:
                    logger.warning(
                        f"Request received a client/server error status code: {response.status_code}. "
                        f"Marking as failed."
                    )
                    failed = True
                    failure_reason = f"Request failed with status code {response.status_code}: {response.reason_phrase}"

                else:
                    logger.info(f"Response received with status code: {response.status_code}")

                body_preview = response.text[:250] + '...' if len(response.text) > 250 else response.text
                logger.debug(f"Response Body Preview: {body_preview}")

                json_body = None
                try:
                    json_body = response.json()
                except (json.JSONDecodeError, ValueError):
                    logger.debug("Response body could not be decoded as JSON.")
                    pass

                meta_tags_data = {}
                json_ld_data = []
                application_json_data = []
                html_body = None
                text_body = None
                soup = None

                # httpx headers are case-insensitive, so 'content-type' works reliably.
                content_type = response.headers.get('content-type', '').lower()

                if 'html' in content_type and response.text:
                    logger.debug(f"Content-type is '{content_type}'. Attempting HTML parse.")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    meta_tags_data = cls._extract_meta_tags(soup)
                    json_ld_data = cls._extract_json_ld(soup)
                    application_json_data = cls._extract_application_json(soup)
                    html_body = response.text
                    text_body = soup.get_text()


                else:
                    logger.debug(f"Content-type is '{content_type}'. Skipping HTML parse.")

                return HTTPResponse(
                    status_code=response.status_code,
                    response_url=str(response.url),
                    response_headers=dict(response.headers),
                    response_cookies=dict(response.cookies),
                    response_time=response.elapsed.total_seconds(),
                    text_body=text_body,
                    json_body=json_body,
                    html_body=html_body,
                    failed=failed,
                    failure_reason=failure_reason,
                    meta_tags_data=meta_tags_data,
                    json_ld_data=json_ld_data,
                    application_json_data=application_json_data,
                    _soup=soup
                )

            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_exception = e
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < request.request_retries:
                    await asyncio.sleep(request.request_retry_delay)
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < request.request_retries:
                    await asyncio.sleep(request.request_retry_delay)

        logger.error(f"All {request.request_retries + 1} request attempts failed for {request.request_url}.")
        return HTTPResponse(
            status_code=0,
            response_url=request.request_url,
            response_headers={},
            response_cookies={},
            response_time=0.0,
            text_body="",
            json_body=None,
            failed=True,
            failure_reason=f"Request failed after {request.request_retries + 1} attempts: {last_exception}"
        )
