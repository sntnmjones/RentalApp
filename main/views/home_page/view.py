import logging
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render

from main.forms.home_page.forms import GetPropertyAddressForm


logger = logging.getLogger()


def index(request):
    if request.method == "POST":
        if request.POST.get("property_address"):
            return _get_property_address(request)
    else:
        get_property_address_form = GetPropertyAddressForm()
        return render(
            request,
            template_name="main/templates/home_page/index.html",
            context={"show_property_address": False,
                    "get_property_address_form": get_property_address_form },
            status=200,
        )


def _get_property_address(request):
    form = GetPropertyAddressForm(request.POST)
    if form.errors:
        logger.error(
            "Error creating GetPropertyAddressForm form: %s", form.errors.as_text
        )
    if form.is_valid():
        address = form.cleaned_data["property_address"]
        logger.info("Getting Address: [%s]", address)

        # Find the address
        property_found = False

        if property_found:
            None
        else:
            logger.info("Address not found: [%s]", address)
            return render(
                request,
                template_name="main/templates/home_page/index.html",
                context={
                    "address": form.cleaned_data["property_address"],
                    "property_found": False,
                    "show_property_address": True,
                    "get_property_address_form": form
                },
                status=200,
            )