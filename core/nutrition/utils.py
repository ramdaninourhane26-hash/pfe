from reportlab.pdfgen import canvas
from django.http import HttpResponse


def generate_plan_pdf(plan):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{plan.name}.pdf"'

    p = canvas.Canvas(response)

    p.drawString(100, 800, plan.name)

    y = 750
    for meal in plan.meals.all():
        p.drawString(100, y, f"{meal.type}: {meal.description}")
        y -= 20

    p.save()
    return response