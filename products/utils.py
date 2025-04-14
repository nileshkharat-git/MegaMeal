import os
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def genrate_html_file(order, items):
    items_rows = "".join(f"<tr><td>{item.product.name}</td><td>{item.quantity}</td><td>{item.price} &#8377;</td></tr>" for item in items)

    html_content = f"""
        <html lang="en">
<head>
    
</head>
<body>
    <h1>Order Confirmed</h1>
    <h2>Order summary</h2>
    <p>Customer Name: {order.customer_name}</p>
    <p>Shipping Address: {order.shipping_address}</p>
    <table border="1" text-align="center">
        <thead>
            <tr>
                <th>Product</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
        </thead>
        <tbody>           
              {items_rows}  
            <tr>
                <td >Subtotal</td>
                <td colspan="2" text-align="right">{order.subtotal} &#8377;</td>
            </tr>
            <tr>
                <td>Delivery charge</td>
                <td colspan="2" text-align="right">{order.delivery_charge} &#8377;</td>
            </tr>
            <tr>
                <td>Discount</td>
                <td colspan="2" text-align="right">{order.discount} &#8377;</td>
            </tr>
            <tr>
                <td>Total</td>
                <td colspan="2" text-align="right">{order.total} &#8377;</td>
            </tr>
        </tbody>
    </table>   
</body>
</html>
    """

    with open("invoice.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    return "invoice.html"

def genrate_html_file_for_orders(orders):
    
    table_rows ="".join(f"\
                    <tr><td>{order.id}</td><td>{order.customer_name}</td>\
                    <td>{','.join(item.product.name for item in order.items.all())}</td>\
                    <td>{','.join(str(item.quantity) for item in order.items.all())}</td>\
                    <td>{','.join(str(item.product.price) for item in order.items.all())}</td>\
                    <td>{order.subtotal}</td><td>{order.delivery_charge}</td>\
                    <td>{order.discount}</td><td>{order.total}</td></tr>"\
                        for order in orders)
    
    html_content = f"""<html lang="en">
                        <head>
                            
                        </head>
                        <body>
                            <h1 align="center">Order report</h1>
                            <table border="1" text-align="center">
                                <thead>
                                    <tr>
                                        <th>Order id</th>
                                        <th>Customer name</th>
                                        <th>Products</th>
                                        <th>Quantity</th>
                                        <th>Price</th>
                                        <th>Subtotal</th>
                                        <th>Delivery charge</th>
                                        <th>Discount</th>
                                        <th>Total</th>
                                    </tr>
                                </thead>
                                <tbody>           
                                    {table_rows}
                                </tbody>
                            </table>   
                        </body>
                        </html>"""

    with open("invoice.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    return "invoice.html"

def convert_html_to_pdf(html_file):
    pdf_file = "invoice.pdf"
    os.system(f'google-chrome --headless --print-to-pdf={pdf_file} {html_file}')
    return pdf_file

def send_email_html(order, items, from_email, recipient_list, subject='Confirmation on order placed'):

    html_content = render_to_string("sendEmail.html", {"items":items, "order":order})
    
    email = EmailMessage(subject=subject, body=html_content, from_email=from_email, to=recipient_list)
    email.content_subtype = "html"
    email.send()

def send_email_pdf(order, items, recipient_list,\
                    subject='Order confirmed', from_email=settings.EMAIL_HOST_USER):

    html_file = genrate_html_file(order=order, items=items)
    pdf_invoice = convert_html_to_pdf(html_file)

    email = EmailMessage(subject=subject, body="Please find invoce attched below", from_email=from_email, to=recipient_list)
    
    with open(pdf_invoice, "rb") as file:
        email.attach("invoice.pdf", file.read(), "application/pdf")

    email.send()

def send_order_report_email(orders, recipient_list):
    html_file = genrate_html_file_for_orders(orders)
    pdf_report = convert_html_to_pdf(html_file)

    email = EmailMessage(subject='Order report', body='Please find report attched below', from_email=settings.EMAIL_HOST_USER, to=recipient_list)
    
    with open(pdf_report, "rb") as file:
        email.attach("invoice.pdf", file.read(), "application/pdf")

    email.send()

