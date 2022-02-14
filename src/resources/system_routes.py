from flask_restful import Resource
from werkzeug import serving

# Import logging controller for log_request function
parent_log_request = serving.WSGIRequestHandler.log_request


# Function for disabling logging on '/'
def log_request(self, *args, **kwargs):
    if self.path == "/healthcheck":
        return

    parent_log_request(self, *args, **kwargs)


class system_health_check(Resource):
    def get(self):
        serving.WSGIRequestHandler.log_request = log_request
        return {"message": "ok"}
