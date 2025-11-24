# -*- coding: utf-8 -*-

from odoo import models, fields, api


class autenticacions(models.Model):
    _name = 'logweb.autenticacions'
    _description = 'autenticacions en GNU/Linux'
    _order = "continente,pais,ip asc"

    # name = fields.Char()
   # quenda = fields.Selection([('Ordinario', 'Ordinario'), ('Vespertino', 'Vespertino'), ('FPDual', 'FPDual')], string='Quenda')
    continente = fields.Char(required=True, size=25, string="Continente")
    pais = fields.Char(required=True, size=25, string="País")
    ip = fields.Char(required=True, size=15, string="IP")
    intentosDeAcceso = fields.Integer(required=True, string="Intentos de Acceso")
    cantidade = fields.Char(compute="_cantidade",size=15, store=True)

    @api.depends('intentosDeAcceso')
    def _cantidade(self):
        for rexistro in self:
            if rexistro.intentosDeAcceso > 50:
                rexistro.cantidade = "Máis de 50"
            elif rexistro.intentosDeAcceso > 9:
                rexistro.cantidade = "Entre 50 e 10"
            else:
                rexistro.cantidade = "Menos de 10"
