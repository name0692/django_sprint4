from django.shortcuts import render
from django.views import View


class AboutView(View):
    template_name = 'pages/about.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class RulesView(View):
    template_name = 'pages/rules.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


def csrf_failure_handler(request, *args, **kwargs):
    return render(request, 'pages/403csrf.html', status=403)


def page_not_found_handler(request, *args, **kwargs):
    return render(request, 'pages/404.html', status=404)


def server_error_handler(request, *args, **kwargs):
    return render(request, 'pages/500.html', status=500)
