"""FCU course availability watcher for Selenium 4.

This program only performs an add-course click when --confirm-enroll is supplied.
It never saves the supplied account credentials.
"""

import argparse
import getpass
import os
import sys
from time import sleep
from typing import Optional

from fcu_course import (
    CourseConfig,
    is_successful_enrollment_response,
    normalize_course_codes,
    parse_seat_status,
    split_enrollment_responses,
    unrecognized_status_message,
)


MAIN_URL = "https://course.fcu.edu.tw/"
SELECTED_TAB_ID = "ctl00_MainContent_TabContainer1_tabSelected_Label3"
COURSE_CODE_INPUT_ID = "ctl00_MainContent_TabContainer1_tabSelected_tbSubID"
QUERY_BUTTON = (
    "#ctl00_MainContent_TabContainer1_tabSelected_gvToAdd "
    "tbody tr:nth-child(2) td:nth-child(8) input"
)
ADD_BUTTON = (
    "#ctl00_MainContent_TabContainer1_tabSelected_gvToAdd "
    "tbody tr:nth-child(2) td:nth-child(1) input"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check FCU course availability.")
    parser.add_argument(
        "--course-code",
        required=True,
        nargs="+",
        help="one or more 4-digit FCU course codes, in priority order",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3,
        help="seconds between checks; 0 disables waiting (default: 3)",
    )
    parser.add_argument(
        "--max-checks",
        type=int,
        default=100,
        help="maximum full sweeps of the remaining courses before stopping (default: 100)",
    )
    parser.add_argument(
        "--confirm-enroll",
        action="store_true",
        help="allow one add-course click after availability is detected",
    )
    return parser.parse_args()


def load_selenium():
    try:
        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException, WebDriverException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as error:
        raise RuntimeError(
            "Selenium is missing. Install dependencies with: pip install -r requirements.txt"
        ) from error
    return webdriver, TimeoutException, WebDriverException, By, EC, WebDriverWait


def get_credentials() -> tuple[str, str]:
    username = os.environ.get("FCU_USERNAME") or input("FCU account: ").strip()
    password = os.environ.get("FCU_PASSWORD") or getpass.getpass("FCU password: ")
    if not username or not password:
        raise ValueError("FCU account and password are required")
    return username, password


def open_login_page(browser, by, wait) -> None:
    browser.get(MAIN_URL)
    wait.until(lambda driver: driver.find_element(by.ID, "ctl00_Login1_UserName"))


def get_captcha_code(prompt=input) -> str:
    captcha_code = prompt("Enter the captcha shown in Chrome: ").strip()
    if not captcha_code:
        raise ValueError("captcha code is required")
    return captcha_code


def login(browser, by, wait, username: str, password: str, captcha_code: str) -> None:
    browser.find_element(by.ID, "ctl00_Login1_UserName").send_keys(username)
    browser.find_element(by.ID, "ctl00_Login1_Password").send_keys(password)
    browser.find_element(by.ID, "ctl00_Login1_vcode").send_keys(captcha_code)
    browser.find_element(by.ID, "ctl00_Login1_LoginButton").click()
    wait.until(lambda driver: selection_page_is_ready(driver, by))


def selection_page_is_ready(browser, by) -> bool:
    return bool(browser.find_elements(by.ID, SELECTED_TAB_ID))


def query_status(
    browser, by, ec, wait, course_code: str
) -> tuple[Optional[tuple[int, int]], str]:
    wait.until(ec.element_to_be_clickable((by.ID, SELECTED_TAB_ID))).click()
    course_input = wait.until(ec.visibility_of_element_located((by.ID, COURSE_CODE_INPUT_ID)))
    course_input.clear()
    course_input.send_keys(course_code)
    wait.until(ec.element_to_be_clickable((by.CSS_SELECTOR, QUERY_BUTTON))).click()
    alert = wait.until(ec.alert_is_present())
    message = alert.text
    alert.accept()
    return parse_seat_status(message), message


def submit_add_request(browser, by, ec, wait) -> str:
    wait.until(ec.element_to_be_clickable((by.CSS_SELECTOR, ADD_BUTTON))).click()
    alert = wait.until(ec.alert_is_present())
    message = alert.text
    alert.accept()
    return message


def wait_between_status_queries(sleep_fn, interval_seconds: int) -> None:
    """Rate-limit queries without reloading a page that may still own an alert."""

    sleep_fn(interval_seconds)


def wait_for_user_confirmation(prompt=input) -> None:
    prompt("Press Enter after verifying the enrolled-course list to close Chrome.")


def main() -> int:
    args = parse_args()
    course_codes = list(normalize_course_codes(args.course_code))
    config = CourseConfig(course_codes[0], args.interval)
    if args.max_checks < 1:
        raise ValueError("max checks must be at least 1")

    webdriver, timeout_error, web_driver_error, by, ec, web_driver_wait = load_selenium()
    username, password = get_credentials()
    options = webdriver.ChromeOptions()
    browser = None

    try:
        browser = webdriver.Chrome(options=options)
        wait = web_driver_wait(browser, 12)
        try:
            open_login_page(browser, by, wait)
            captcha_code = get_captcha_code()
            login(browser, by, wait, username, password, captcha_code)
        except timeout_error:
            print(
                "Login did not reach the course-selection page. "
                "Check your credentials, manually entered captcha, system notice, and Chrome page."
            )
            return 2

        pending_course_codes = course_codes.copy()
        submitted_responses = {}

        for sweep in range(1, args.max_checks + 1):
            for course_code in pending_course_codes.copy():
                try:
                    status, message = query_status(browser, by, ec, wait, course_code)
                except timeout_error:
                    print(
                        f"[{sweep}/{args.max_checks}] {course_code}: "
                        "no course-status alert; stop and inspect page"
                    )
                    return 2

                if status is None:
                    print(f"[{sweep}/{args.max_checks}] {unrecognized_status_message(course_code, message)}")
                    return 2

                remaining, open_seats = status
                print(
                    f"[{sweep}/{args.max_checks}] {course_code}: "
                    f"remaining={remaining}, open={open_seats}"
                )
                if remaining > 0:
                    if not args.confirm_enroll:
                        print(
                            f"Seat found for {course_code}. No add request sent: rerun with "
                            "--confirm-enroll to allow one request per course."
                        )
                        return 0

                    result = submit_add_request(browser, by, ec, wait)
                    submitted_responses[course_code] = result
                    pending_course_codes.remove(course_code)
                    if is_successful_enrollment_response(result):
                        print(f"{course_code}: add-course success. Continue with remaining courses.")
                    else:
                        print(
                            f"{course_code}: add request submitted but response was not explicit success. "
                            "This course will not be submitted again in this run."
                        )

                if pending_course_codes:
                    wait_between_status_queries(sleep, config.poll_interval_seconds)

            if not pending_course_codes:
                break

        if submitted_responses:
            confirmed, unconfirmed = split_enrollment_responses(submitted_responses)
            if confirmed:
                print(f"Explicitly successful courses: {', '.join(confirmed)}")
            if unconfirmed:
                print(
                    "Submitted but not explicitly confirmed: "
                    f"{', '.join(unconfirmed)}. Check the enrolled-course list."
                )
            wait_for_user_confirmation()
            return 1 if unconfirmed else 0

        print("No seat found before the configured maximum sweeps.")
        return 1
    except web_driver_error as error:
        print(f"Browser automation failed: {error.msg}")
        return 2
    finally:
        if browser is not None:
            browser.quit()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(2)
