from .models import SchoolSettings

def school_info(request):
    settings = SchoolSettings.objects.first()
    return {'school_settings': settings}