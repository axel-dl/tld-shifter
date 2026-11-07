#!/usr/bin/env python3

import re
import time
import requests


class RateLimiter:
    def __init__(self, requests_per_second: int):
        self.interval = 1.0 / requests_per_second
        self.next_request = 0.0

    def wait(self):
        now = time.monotonic()

        if self.next_request > now:
            time.sleep(self.next_request - now)

        self.next_request = max(
            self.next_request,
            time.monotonic()
        ) + self.interval


def check_http(host, session, limiter):
    for scheme in ("https", "http"):
        url = f"{scheme}://{host}/"

        limiter.wait()

        try:
            with session.get(
                url,
                timeout=5,
                allow_redirects=False,
                stream=True
            ) as response:

                return {
                    "host": host,
                    "status": response.status_code
                }

        except requests.exceptions.RequestException:
            continue

    return None


def main():

    DOMAIN_NAME = input(
        "Domain to shift (without TLD): "
    ).strip().lower().rstrip(".")

    if not DOMAIN_NAME:
        print("Invalid domain.")
        return

    while True:
        try:
            REQS_PER_SEC = int(input("Requests per second: "))

            if REQS_PER_SEC <= 0:
                raise ValueError

            break

        except ValueError:
            print("Enter a positive integer.")

    COMMON_TLDS = [
        # Generic TLDs
        "com", "org", "net", "info", "biz", "xyz",
        "online", "site", "website", "store", "shop",
        "app", "dev", "tech", "cloud", "io", "ai",
        "me", "tv", "pro", "name", "mobi", "live",

        # Business and organization TLDs
        "edu", "gov", "mil", "int", "museum", "coop",
        "aero", "jobs", "travel",

        # Country-code TLDs
        "us", "uk", "co.uk", "de", "fr", "es", "it",
        "nl", "be", "ch", "at", "pl", "se", "no",
        "dk", "fi", "ie", "pt", "gr", "ru", "ua",
        "ca", "mx", "br", "ar", "cl", "co", "pe",
        "jp", "cn", "in", "au", "nz", "kr", "sg",
        "hk", "tw", "id", "my", "th", "vn", "ph",
        "za", "ng", "ke", "eg", "il", "tr",

        # Other TLDs
        "network", "digital", "systems",
        "solutions", "services", "security", "software",
        "technology", "media", "group", "global",
        "world", "company", "agency", "center",
        "email", "support", "academy", "foundation",
        "finance", "page", "tools"
    ]

    COMMON_TLDS = list(dict.fromkeys(COMMON_TLDS))

    limiter = RateLimiter(REQS_PER_SEC)
    checked = set()
    valid_count = 0

    output_file = f"{DOMAIN_NAME}-tld-shifter.txt"

    with requests.Session() as session:

        session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Recon/1.0)"
        })

        with open(output_file, "w", encoding="utf-8") as output:

            def save_domain(domain):
                nonlocal valid_count

                output.write(domain + "\n")
                output.flush()
                valid_count += 1

            print(f"\n[*] Target: {DOMAIN_NAME}")
            print(f"[*] Rate limit: {REQS_PER_SEC} req/s")
            print(f"[*] Output: {output_file}\n")

            for tld in COMMON_TLDS:

                candidate = f"{DOMAIN_NAME}.{tld}"

                if candidate in checked:
                    continue

                checked.add(candidate)

                print(f"[>] {candidate}")

                result = check_http(
                    candidate, session, limiter
                )

                if not result:
                    continue

                save_domain(candidate)

                print(f"[+] Valid: {candidate}")

                for second_tld in COMMON_TLDS:

                    second_candidate = f"{candidate}.{second_tld}"

                    if second_candidate in checked:
                        continue

                    checked.add(second_candidate)

                    print(f"[>] {second_candidate}")

                    second_result = check_http(
                        second_candidate,
                        session,
                        limiter
                    )

                    if second_result:
                        save_domain(second_candidate)
                        print(f"[+] Valid: {second_candidate}")

    print(f"\n[*] Completed.")
    print(f"[*] Valid domains: {valid_count}")
    print(f"[*] Saved to: {output_file}")


if __name__ == "__main__":
    main()