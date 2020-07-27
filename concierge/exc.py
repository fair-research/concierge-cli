import json
import globus_sdk


class ConciergeException(globus_sdk.exc.GlobusAPIError):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.errors = json.loads(self.message)
        except Exception:
            self.errors = {'server_error': self.message}
