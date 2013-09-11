from django.http import HttpResponse
from django.views.generic.base import View

class FrameView(View):
    def get(self, request):
        # <view logic>
        result = ''
        return HttpResponse(result)
