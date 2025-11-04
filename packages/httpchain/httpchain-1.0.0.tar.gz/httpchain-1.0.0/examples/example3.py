import asyncio
import json
from dataclasses import asdict
import logging
import sys

import tldextract

from httpchain import HttpChainExecutor

logger = logging.getLogger("httpchain")


def setup_logger(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def find_registry_url(domain, bootstrap_data):
    extracted = tldextract.extract(domain)
    suffix = extracted.suffix.lower()

    # Get the actual TLD (last part after splitting by dots)
    # "co.uk" -> "uk", "com.au" -> "au", "com" -> "com"
    actual_tld = suffix.split('.')[-1] if suffix else None

    if not actual_tld:
        return None
    try:
        tld_punycode = actual_tld.encode('idna').decode('ascii')
    except Exception:
        tld_punycode = actual_tld

    for service in bootstrap_data:
        if len(service) >= 2:
            tlds, endpoints = service[0], service[1]
            if (actual_tld in tlds or tld_punycode in tlds) and endpoints:
                endpoint = endpoints[0].rstrip('/')
                return endpoint

    print(f"No registry found for TLD: {actual_tld} / {tld_punycode}")
    return None

async def main():
    setup_logger(False)
    domain = "claude.ai"
    try:
        domain_punycode = domain.encode('idna').decode('ascii')
        print(f"Domain punycode: {domain_punycode}")
    except Exception:
        domain_punycode = domain

    with open("osint/domain_lookup_registry.json") as f:
        registry_chain = json.load(f)

    executor = HttpChainExecutor()
    executor.load_json(registry_chain)
    result1 = await executor.execute()

    bootstrap_data = result1._variable_state.get("bootstrap_registry", [])
    registry_url = find_registry_url(domain, bootstrap_data)

    with open("osint/domain_lookup.json") as f:
        domain_chain = json.load(f)

    executor = HttpChainExecutor()
    executor.load_json(domain_chain)
    result2 = await executor.execute(domain=domain_punycode, registry_url=registry_url)

    for source in ['authoritative', 'fallback_1', 'fallback_2', 'fallback_3']:
        if result2.variable_state_dict.get(f"{source}_success"):
            data = result2.variable_state_dict.get(f"{source}_data")
            print(f"Success via {source}: {data.get('ldhName')}")
            break
    else:
        print("All sources failed")

    with open("output/domain_lookup_output.json", "w") as f:
        json.dump(asdict(result2), f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
