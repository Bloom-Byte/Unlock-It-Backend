from random import choices, shuffle
import string
import json

from datetime import timedelta

import imghdr
import base64
from io import BytesIO

import requests


from django.core.paginator import Paginator
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from django.utils import timezone

from rest_framework.response import Response

from app.enum_classes import OTPStatuses

from app.models import OTP


def snake_case_to_camel_case(value: str):
    splitted_string = value.split("_")

    camel_string = splitted_string.pop(0)

    for other_words in splitted_string:
        camel_string += other_words.title()

    return camel_string


class APIResponses:
    @classmethod
    def success_response(cls, message: str, status_code, data=None, paginate_data=None):
        context = {
            "message": message,
        }

        if data is not None:
            context["data"] = data

            if paginate_data:
                context["pagination"] = paginate_data

        return Response(context, status=status_code)

    @classmethod
    def error_response(cls, status_code, message, errors: dict = None):
        context = {
            "message": message,
        }

        if errors is not None:
            errors_list = []
            for key, value in errors.items():
                if isinstance(value, list):
                    value = value[0]

                key = snake_case_to_camel_case(key)

                errors_list.append({"fieldName": key, "error": value})

            context["errors"] = errors_list

        return Response(context, status=status_code)

    @classmethod
    def server_error(cls, message: str, status_code):
        context = {"message": message}

        return Response(context, status=status_code)


class CodeGenerator:
    @staticmethod
    def generate_code():
        if not settings.GENERATE_CODE:
            code = settings.DEFAULT_OTP

        else:
            code = "".join(choices(string.digits, k=6))

        return code

    @staticmethod
    def generate_default_password():
        total_password = []

        upper_letters = choices(string.ascii_uppercase, k=3)
        lower_letters = choices(string.ascii_lowercase, k=3)
        numbers = choices(string.digits, k=2)
        alpha_numerics = choices(
            [
                "!",
                "@",
                "#",
                "$",
                "%",
                "&",
                "*",
                "+",
                "=",
            ],
            k=2,
        )

        total_password.extend(upper_letters)
        total_password.extend(lower_letters)
        total_password.extend(numbers)
        total_password.extend(alpha_numerics)

        shuffle(total_password)

        default_password = "".join(total_password)

        return default_password

    @staticmethod
    def generate_transaction_reference():
        upper = choices(string.ascii_uppercase, k=7)
        digits = choices(string.digits, k=7)
        total = upper + digits

        return "".join(total)

    @staticmethod
    def generate_referral_code():
        upper = choices(string.ascii_uppercase, k=4)
        digits = choices(string.digits, k=4)
        total = upper + digits

        shuffle(total)

        return "".join(total)

    @staticmethod
    def generate_story_reference():
        upper = choices(string.ascii_letters, k=4)
        digits = choices(string.digits, k=4)
        total = upper + digits

        shuffle(total)

        return "RN-" + "".join(total)


class MyPagination:
    @classmethod
    def get_paginated_response(
        cls, request, queryset, page_size_param="page_size", page_number_param="page"
    ):
        page_number = request.query_params.get(page_number_param, 1)
        page_size = request.query_params.get(page_size_param, 25)

        paginator = Paginator(queryset, page_size)
        try:
            current_page = paginator.page(page_number)
        except Exception:
            return None, None, "Invalid page number"

        total_data = {
            "itemsCount": queryset.count(),
            "currentPage": current_page.number,
            "numberOfPages": paginator.num_pages,
            "nextPage": current_page.next_page_number() if current_page.has_next() else None,
            "previousPage": (
                current_page.previous_page_number() if current_page.has_previous() else None
            ),
        }

        return total_data, current_page.object_list, None


# class DateHelper:
#     @staticmethod
#     def get_next_date(day: str, c_time=None):
#         now = pendulum.now()
#         if day == "Monday":
#             next_date = now.next(pendulum.MONDAY).date()
#         elif day == "Tuesday":
#             next_date = now.next(pendulum.TUESDAY).date()
#         elif day == "Wednesday":
#             next_date = now.next(pendulum.WEDNESDAY).date()
#         elif day == "Thursday":
#             next_date = now.next(pendulum.THURSDAY).date()
#         elif day == "Friday":
#             next_date = now.next(pendulum.FRIDAY).date()
#         elif day == "Saturday":
#             next_date = now.next(pendulum.SATURDAY).date()
#         elif day == "Sunday":
#             next_date = now.next(pendulum.SUNDAY).date()
#         else:
#             next_date = now.next(pendulum.MONDAY).date()  # defaults to monday

#         if c_time:
#             return datetime.combine(next_date, time(c_time.hour, c_time.minute))

#         return next_date

#     @staticmethod
#     def get_date_filter(date_filter: DateFilterBy):
#         today_date = timezone.now().date()

#         if date_filter == DateFilterBy.TODAY:
#             return today_date, today_date

#         if date_filter == DateFilterBy.YESTERDAY:
#             yesterday = today_date - timedelta(days=1)

#             return yesterday, yesterday

#         if date_filter == DateFilterBy.THIS_WEEK:
#             today_pendulum = pendulum.now()

#             start_week = today_pendulum.previous(pendulum.SUNDAY).date()

#             return start_week, today_pendulum.date()

#         if date_filter == DateFilterBy.LAST_WEEK:
#             today_pendulum = pendulum.now()

#             start_date = today_pendulum.previous(pendulum.SUNDAY).subtract(weeks=1).date()
#             end_date = today_pendulum.next(pendulum.SATURDAY).subtract(weeks=1).date()

#             return start_date, end_date

#         if date_filter == DateFilterBy.THIS_MONTH:
#             today_pendulum = pendulum.now()

#             start_date = today_pendulum.start_of("month").date()

#             return start_date, today_pendulum.date()

#         if date_filter == DateFilterBy.LAST_MONTH:
#             today_pendulum = pendulum.now()

#             start_date = today_pendulum.subtract(months=1).start_of("month").date()
#             end_date = today_pendulum.subtract(months=1).end_of("month").date()

#             return start_date, end_date

#         if date_filter == DateFilterBy.LAST_3_MONTH:
#             today_pendulum = pendulum.now()

#             start_date = today_pendulum.subtract(months=3).start_of("month").date()

#             return start_date, today_pendulum.date()

#     @staticmethod
#     def get_last_month_date():
#         previous_month = pendulum.now().subtract(months=1).date()

#         return previous_month

#     @staticmethod
#     def get_day_name(day_number: int):
#         day_dict = {
#             1: "Sunday",
#             2: "Monday",
#             3: "Tuesday",
#             4: "Wednesday",
#             5: "Thursday",
#             6: "Friday",
#             7: "Saturday",
#         }

#         return day_dict[int(day_number)]

#     @staticmethod
#     def get_current_week():
#         # resumption date
#         resumption_date_object = SystemConfig.objects.filter(
#             name=SystemConfigKeys.RESUMPTION_DATE
#         ).first()

#         # vacation date
#         vacation_date_object = SystemConfig.objects.filter(
#             name=SystemConfigKeys.VACATION_DATE
#         ).first()

#         if resumption_date_object and vacation_date_object:
#             today = timezone.now().date().strftime("%Y-%m-%d")

#             start_date = datetime.strptime(resumption_date_object.value, "%Y-%m-%d")
#             end_date = datetime.strptime(vacation_date_object.value, "%Y-%m-%d")

#             weeks_data = {}

#             current_date = start_date
#             week_number = 1

#             while current_date <= end_date:
#                 week_end = current_date + timedelta(days=6)
#                 week_dates = []

#                 while current_date <= week_end and current_date <= end_date:
#                     week_dates.append(current_date.strftime("%Y-%m-%d"))
#                     current_date += timedelta(days=1)

#                 week_name = f"Week {week_number}"
#                 weeks_data[week_name] = week_dates
#                 week_number += 1

#             for week_name, week_range in weeks_data.items():
#                 if today in week_range:
#                     return week_name

#         return "Week 1"

#     @staticmethod
#     def get_current_day():
#         today = timezone.now().date().strftime("%A")

#         return today


# class ExportHelper:
#     @classmethod
#     def draw_as_table(cls, df, pagesize, column_widths):
#         alternating_colors = [["white"] * len(df.columns), ["lightgray"] * len(df.columns)] * len(
#             df
#         )
#         alternating_colors = alternating_colors[: len(df)]
#         fig, ax = plt.subplots(figsize=pagesize)
#         ax.axis("tight")
#         ax.axis("off")
#         ax.table(
#             cellText=df.values,
#             rowLabels=df.index,
#             colLabels=df.columns,
#             rowColours=["lightblue"] * len(df),
#             colColours=["lightblue"] * len(df.columns),
#             cellColours=alternating_colors,
#             loc="top",
#             colWidths=column_widths,
#         )
#         return fig

#     @classmethod
#     def generate_pdf(cls, df, buffer, column_widths, rows_per_page=100, pagesize=(8.5, 11)):
#         with PdfPages(buffer) as pdf:
#             # nh, nv = num_pages
#             nh = math.ceil(len(df) / rows_per_page)
#             nv = 1

#             # rows_per_page = math.ceil(len(df) / nh)
#             cols_per_page = math.ceil(len(df.columns) / 1)

#             for i in range(0, nh):
#                 for j in range(0, nv):
#                     page = df.iloc[
#                         (i * rows_per_page) : min((i + 1) * rows_per_page, len(df)),
#                         (j * cols_per_page) : min((j + 1) * cols_per_page, len(df.columns)),
#                     ]
#                     fig = cls.draw_as_table(page, pagesize, column_widths=column_widths)

#                     if nh > 1 or nv > 1:
#                         # Add a part/page number at bottom-center of page
#                         fig.text(
#                             0.5,
#                             0.5 / pagesize[0],
#                             f"Part-{i+1}x{j+1}: Page-{i * nv + j + 1}",
#                             ha="center",
#                             fontsize=8,
#                         )
#                     pdf.savefig(fig, bbox_inches="tight")

#                     plt.close()

#         return buffer

#     @classmethod
#     def export_list_data(
#         cls,
#         data_list: list,
#     ):
#         data_frame = pandas.DataFrame(data=data_list)
#         data_frame.index += 1

#         buffer = BytesIO()

#         data_frame.to_excel(buffer)

#         buffer.seek(0)
#         final_data = base64.b64encode(buffer.read()).decode()

#         return final_data


class SMSSender:
    @staticmethod
    def send_sms(receiver: str, message: str):
        pass

    # TODO come back to this
    # if receiver.startswith("0"):
    #     receiver = receiver[1:]
    #     receiver = f"234{receiver}"

    # KUDISMS_BASE_URL = "https://my.kudisms.net/api/sms"

    # data = {
    #     "token": settings.KUDISMS_AUTH_TOKEN,
    #     "senderID": settings.KUDISMS_SENDER_ID,
    #     "recipients": receiver,
    #     "message": message,
    #     "gateway": "2",
    # }

    # print(f"Data to be sent to KUDISMS is {data}")

    # headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # response = requests.get(
    #     url=KUDISMS_BASE_URL, data=data, params=data, headers=headers, timeout=60
    # )

    # result_dict = response.json()

    # print(f"Response from KUDISMS is {result_dict=}")


class EmailSender:
    @staticmethod
    def send_password_reset_email(receiver, otp):
        pass


class OTPHelper:
    @classmethod
    def throttle_otp(cls, recipient, purpose):
        """
        Method for determining wether to allow creation of another otp based on the recipient and the purpose

        Params:
            recipient: an object of the user model
            purpose: the purpose of the otp

        Returns:
            True -> if creation of another otp should be allowed
            False -> if creation of another otp should be denied
        """

        otp_object = OTP.objects.filter(purpose=purpose).filter(recipient=recipient).first()

        if otp_object is None:
            # there is no previous otp, so creation is allowed
            return True

        # there is an otp, compare the time it was created with the current time, to make sure it has passed the period

        if otp_object.created_at < timezone.now().now() + timedelta(
            minutes=settings.OTP_GENERATE_TIME_LAPSE_MINUTES
        ):
            # created_at is lower then the current time, so don't create new otp
            return False

        return True

    @classmethod
    def generate_otp(cls, purpose, channel, recipient):
        code = CodeGenerator.generate_code()

        new_otp = OTP()
        new_otp.otp = code
        new_otp.purpose = purpose
        new_otp.status = OTPStatuses.ACTIVE
        new_otp.channel = channel
        new_otp.recipient = recipient
        new_otp.expire_at = timezone.now().now() + timedelta(
            minutes=settings.OTP_EXPIRATION_MINUTES
        )

        new_otp.save()

        return code

    @classmethod
    def send_otp(cls, purpose, recipient, email=None, phone_number=None):
        # try to see if an otp for this purpose exists already
        previous_otps = (
            OTP.objects.filter(recipient=recipient)
            .filter(purpose=purpose)
            .filter(status=OTPStatuses.ACTIVE)
            # .filter(expire_at__lte=timezone.now().now())  # add this
        )

        previous_otps.update(status=OTPStatuses.INACTIVE)

        code = CodeGenerator.generate_code()

        new_otp = OTP()
        new_otp.otp = code
        new_otp.purpose = purpose
        new_otp.status = OTPStatuses.ACTIVE
        new_otp.recipient = recipient
        new_otp.expire_at = timezone.now().now() + timedelta(
            minutes=settings.OTP_EXPIRATION_MINUTES
        )

        new_otp.save()

        if not settings.DEBUG:
            # DEBUG is false

            if email:
                # send to email address
                EmailSender.send_otp_email(receiver=recipient, otp_code=code)

            if phone_number:
                # TODO add message here
                SMSSender.send_sms(receiver=recipient, message=code)

        return code

    @classmethod
    def verify_otp(cls, otp, purpose, recipient, mark_used=False):
        # update the otp model
        otp_object = (
            OTP.objects.filter(status=OTPStatuses.ACTIVE)
            .filter(recipient=recipient)
            .filter(purpose=purpose)
            .first()
        )

        if otp_object:
            if otp == otp_object.otp:
                if otp_object.expire_at <= timezone.now():
                    otp_object.status = OTPStatuses.EXPIRED
                    otp_object.save()
                    return False

                if mark_used:
                    otp_object.status = OTPStatuses.USED

                otp_object.verified = True
                otp_object.save()

                return True

            return False

        return False

    @classmethod
    def check_verified(cls, otp, purpose, recipient):
        # update the otp model
        otp_object = (
            OTP.objects.filter(status=OTPStatuses.ACTIVE)
            .filter(recipient=recipient)
            .filter(purpose=purpose)
            .first()
        )

        if otp_object:
            if otp == otp_object.otp:
                return otp_object.verified

            return False

        return False


class FileHelper:
    @staticmethod
    def convert_base64_to_file(base64_file: str, file_name: str = None):
        try:
            base_header = base64_file.split("base64")[0]
            base_str = base64_file.split("base64")[1][1:]
        except Exception:
            print("Exception when validating the file")
            return None

        file_bytes = base64.b64decode(base_str)

        if "pdf" in base_header:
            extension = "pdf"
            content_type = "application/pdf"

        elif "image" in base_header:
            extension = imghdr.what(None, file_bytes)
            content_type = f"image/{extension}"

        if file_name is None:
            file_name = f"{timezone.now()}.{extension}"

        file_stream = BytesIO()
        file_stream.write(file_bytes)
        file_size = file_stream.tell()
        file_stream.seek(0)

        file_upload = InMemoryUploadedFile(
            file=file_stream,
            field_name=None,
            content_type=content_type,
            size=file_size,
            charset=None,
            name=file_name,
        )

        return file_upload

    @staticmethod
    def get_file_details(base64_file: str):
        try:
            base_header = base64_file.split("base64")[0]
            base_str = base64_file.split("base64")[1][1:]

        except Exception:
            return False, None

        file_bytes = base64.b64decode(base_str)

        if "pdf" in base_header:
            file_type = "PDF"

        else:
            file_type = "IMAGE"

        file_stream = BytesIO()
        file_stream.write(file_bytes)

        file_size = (file_stream.tell() / 1024) / 1024

        return True, (file_size, file_type)


#     # @staticmethod
#     # def convert_to_base_64(file_upload: InMemoryUploadedFile):
#     #     # Get the MIME type of the file
#     #     if hasattr(file_upload, "content_type"):
#     #         mime_type = file_upload.content_type
#     #     else:
#     #         # Fall back to mimetypes if content_type is not available
#     #         mime_type, _ = mimetypes.guess_type(file_upload.name)

#     #     if mime_type:
#     #         file_data = file_upload.read()
#     #         base64_encoded = base64.b64encode(file_data).decode("utf-8")
#     #         data_uri = f"data:{mime_type};base64,{base64_encoded}"
#     #         return data_uri

#     #     return None


class PaymentProviderHelper:
    @staticmethod
    def get_paystack_banks():
        url = "https://api.paystack.co/bank"

        headers = {
            "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "content-type": "application/json",
        }

        query_params = {"perPage": 100, "country": "nigeria", "currency": "NGN"}

        response = requests.get(
            url=url,
            headers=headers,
            params=query_params,
            timeout=settings.REST_CALL_TIMEOUT_SECONDS,
        )

        response_json: dict = response.json()

        total_data = []

        for item in response_json["data"]:
            total_data.append({"name": item["name"], "code": item["code"]})

        return total_data

    @staticmethod
    def resolve_account_number(account_number: str, bank_code: str):
        url = "https://api.paystack.co/bank/resolve"

        headers = {
            "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "content-type": "application/json",
        }

        query_params = {"account_number": account_number, "bank_code": bank_code}

        response = requests.get(
            url=url,
            headers=headers,
            params=query_params,
            timeout=settings.REST_CALL_TIMEOUT_SECONDS,
        )

        response_json: dict = response.json()

        if response_json["status"]:
            # verification successful
            account_name = response_json["data"]
            return False, account_name

        return True, None

    @staticmethod
    def generate_paystack_payment_link(amount: float, email: str, reference: str):
        url = "https://api.paystack.co/transaction/initialize"

        payload = {
            "amount": amount * 100,
            "email": email,
            "reference": reference,
        }

        headers = {
            "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "content-type": "application/json",
        }

        response = requests.post(
            url=url,
            data=json.dumps(payload),
            headers=headers,
            timeout=120,
        )

        response_json: dict = response.json()

        if response_json["status"] is True:
            return response_json["data"]["authorization_url"]

        print(f"Unable to generate paystack payment link: {response_json}")
        return None

    @staticmethod
    def verify_transaction_status(transaction_id: str):
        return {}
