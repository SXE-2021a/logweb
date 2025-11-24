# -*- coding: utf-8 -*-
# from odoo import http


# class Odoo2122exame1(http.Controller):
#     @http.route('/odoo_2122exame1/odoo_2122exame1', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odoo_2122exame1/odoo_2122exame1/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('odoo_2122exame1.listing', {
#             'root': '/odoo_2122exame1/odoo_2122exame1',
#             'objects': http.request.env['odoo_2122exame1.odoo_2122exame1'].search([]),
#         })

#     @http.route('/odoo_2122exame1/odoo_2122exame1/objects/<model("odoo_2122exame1.odoo_2122exame1"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odoo_2122exame1.object', {
#             'object': obj
#         })
