import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fcu_course import (
    CourseConfig,
    is_successful_enrollment_response,
    normalize_course_codes,
    parse_seat_status,
    split_enrollment_responses,
    unrecognized_status_message,
)
from FCU_grabbed_class import (
    get_captcha_code,
    selection_page_is_ready,
    wait_between_status_queries,
    wait_for_user_confirmation,
)


class CourseConfigTests(unittest.TestCase):
    def test_accepts_four_digit_course_code_and_zero_poll_interval(self):
        config = CourseConfig(course_code="1459", poll_interval_seconds=0)

        self.assertEqual(config.course_code, "1459")
        self.assertEqual(config.poll_interval_seconds, 0)

    def test_rejects_negative_poll_interval(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            CourseConfig(course_code="1459", poll_interval_seconds=-1)

    def test_normalizes_multiple_codes_in_priority_order_without_duplicates(self):
        self.assertEqual(
            normalize_course_codes(["1459", "1234", "1459", "5678"]),
            ("1459", "1234", "5678"),
        )

    def test_rejects_invalid_code_in_multiple_course_input(self):
        with self.assertRaisesRegex(ValueError, "exactly 4"):
            normalize_course_codes(["1459", "ABCDE"])


class SeatStatusTests(unittest.TestCase):
    def test_parses_labeled_remaining_and_open_seats(self):
        message = "目前剩餘名額：12，開放名額：30"

        self.assertEqual(parse_seat_status(message), (12, 30))

    def test_parses_slash_separated_remaining_and_open_seats(self):
        message = "剩餘名額/開放名額：0 /60"

        self.assertEqual(parse_seat_status(message), (0, 60))

    def test_returns_none_when_message_does_not_contain_both_counts(self):
        self.assertIsNone(parse_seat_status("課程不存在或查詢失敗"))

    def test_formats_unknown_status_with_its_raw_message(self):
        self.assertEqual(
            unrecognized_status_message("1686", "目前沒有符合條件的資料"),
            "1686: unrecognized status message: 目前沒有符合條件的資料",
        )


class ConfirmationFlowTests(unittest.TestCase):
    def test_waits_between_status_queries_without_browser_operations(self):
        sleep_calls = []

        wait_between_status_queries(sleep_calls.append, 3)

        self.assertEqual(sleep_calls, [3])

    def test_waits_for_user_confirmation_after_an_add_request(self):
        prompts = []

        wait_for_user_confirmation(prompts.append)

        self.assertEqual(prompts, ["Press Enter after verifying the enrolled-course list to close Chrome."])


class EnrollmentResponseTests(unittest.TestCase):
    def test_recognizes_successful_add_course_response(self):
        self.assertTrue(is_successful_enrollment_response("加選成功"))

    def test_does_not_treat_full_course_response_as_success(self):
        self.assertFalse(is_successful_enrollment_response("此課程已額滿"))

    def test_does_not_treat_explicit_failure_as_success(self):
        self.assertFalse(is_successful_enrollment_response("加選不成功"))

    def test_separates_confirmed_and_unconfirmed_add_requests(self):
        confirmed, unconfirmed = split_enrollment_responses(
            {"1459": "加選成功", "1234": "系統忙碌，請稍後再試"}
        )

        self.assertEqual(confirmed, ("1459",))
        self.assertEqual(unconfirmed, ("1234",))


class SelectionPageTests(unittest.TestCase):
    class By:
        ID = "id"

    class Browser:
        def __init__(self, elements):
            self.elements = elements

        def find_elements(self, strategy, value):
            self.last_lookup = (strategy, value)
            return self.elements

    def test_identifies_selection_page_when_selected_tab_exists(self):
        browser = self.Browser([object()])

        self.assertTrue(selection_page_is_ready(browser, self.By))
        self.assertEqual(browser.last_lookup, ("id", "ctl00_MainContent_TabContainer1_tabSelected_Label3"))

    def test_rejects_page_without_selected_tab(self):
        self.assertFalse(selection_page_is_ready(self.Browser([]), self.By))


class CaptchaInputTests(unittest.TestCase):
    def test_strips_manual_captcha_input(self):
        self.assertEqual(get_captcha_code(lambda _: "  7Kp9  "), "7Kp9")

    def test_rejects_empty_manual_captcha_input(self):
        with self.assertRaisesRegex(ValueError, "captcha"):
            get_captcha_code(lambda _: "   ")


if __name__ == "__main__":
    unittest.main()
