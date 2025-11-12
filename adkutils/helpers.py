from google_request_helper import GoogleRequestHelper

class DiscoveryEngineRequestHelper(GoogleRequestHelper):
    def __init__(self, project_id, location):
        if location == "global":        
            self.base_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/"
        else:
            self.base_url = f"https://{location}-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/{location}/"
        super().__init__(project_id, self.base_url)            

class AiPlatformRequestHelper(GoogleRequestHelper):
    def __init__(self, project_id, location):
        self.base_url = f"https://aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/"
        super().__init__(project_id, self.base_url)
        
