import smtplib, pygame, threading, os, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from datetime import datetime, timezone


class Notification:
    SOUND_INTERVAL = 0.5
    EMAIL_INTERVAL = 45
    RECEIVERS = []

    def __init__(
        self,
        soundPath: str = "../asset/alert.mp3",
        imagePath: str = "../asset/alert.png",
    ) -> None:
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(soundPath)
            self.soundAvailable = True
        except Exception as e:
            print(f"Failed to initialize sound system: {e}")
            self.soundAvailable = False

        self.soundThreadCheck = threading.Event()
        self.imagePath = imagePath
        self.isActive = False
        self.lastSend = None

    def __setAlarm(self) -> None:
        if self.soundThreadCheck.is_set():
            return  # another thread is already running
        self.soundThreadCheck.set()

        try:
            while self.isActive and self.soundAvailable:
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and self.isActive:
                    time.sleep(self.SOUND_INTERVAL)
        except Exception as e:
            print(f"Sound error: {e}")
        finally:
            self.soundThreadCheck.clear()

    def canSend(self) -> bool:
        if self.lastSend is None:
            return True

        timeleft = (datetime.now(timezone.utc) - self.lastSend).total_seconds()
        return timeleft >= self.EMAIL_INTERVAL

    def __sendMail(self, receivers: list[str]) -> None:
        if not self.canSend():  # put sending email on hold
            return

        load_dotenv()
        sender = os.getenv("OUTLOOK_EMAIL")
        pwd = os.getenv("OUTLOOK_PASSWORD")

        if not sender or not pwd:
            raise ValueError("Email or password is not properly set.")

        msg = MIMEMultipart()
        msg["Subject"] = "⚠ ALERT: Intrusion Detected"
        msg["From"] = str(sender)
        msg["To"] = ", ".join(receivers)
        msg.attach(
            MIMEText(
                """
                Alert! Someone has intruded the restricted area. See the attached image.
                """,
                "plain",
            )
        )

        try:
            with open(self.imagePath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())

            encoders.encode_base64(part)
            filename = os.path.basename(self.imagePath)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
        except FileNotFoundError:
            print(f"File '{self.imagePath}' was not found. Sending without attachment.")

        try:
            with smtplib.SMTP("smtp.office365.com", 587) as server:
                server.starttls()
                server.login(sender, pwd)
                server.sendmail(sender, receivers, msg.as_string())

            self.lastSend = datetime.now(timezone.utc)  # update lastSend on sent
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def toggleAlertSystem(self) -> None:
        self.isActive = not self.isActive  # toggle on/off alarm system
        if not self.isActive:
            return

        if not self.soundThreadCheck.is_set() and self.soundAvailable:
            threading.Thread(target=self.__setAlarm, daemon=True).start()

        threading.Thread(
            target=self.__sendMail, args=(self.RECEIVERS,), daemon=True
        ).start()
