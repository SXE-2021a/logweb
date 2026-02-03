# -*- coding: utf-8 -*-

from odoo import models, fields, api
from pygments.lexer import default

from . import miñasUtilidades
import ipaddress
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


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

    def consultaNaWebIpinfo(self, ip):
        tokenGardadoNaBD = self.env['ir.config_parameter'].sudo().get_param('logweb.tokenParaIpinfo')
        if tokenGardadoNaBD:
            tokenGardadoNaBD = tokenGardadoNaBD.strip()
            url = f"https://api.ipinfo.io/lite/{ip}"
            params = {'token': tokenGardadoNaBD}
            try:
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status()
                return response.json()
            except requests.RequestException:
                return {}
        else:
            return {}

    def cargaIps(self):
        rutaWindowsParaLogDeSaida = 'c:\\users\\antonio\\logs'
        rutaGNULinuxParaLogDeSaida = '/home/antonio/logs'
        dataInicialUltimoProceso = '2000-01-01'
        dataUltimoProceso = fields.Date.from_string(
            self.env['ir.config_parameter'].sudo().get_param('logweb.dataUltimoProcesoAuthLog',
                                                             dataInicialUltimoProceso))
        dataDeOnte = fields.Date.today() - relativedelta(days=1)
        logfile = "/home/antonio/PycharmProjects/logweb/static/auth.log"
        #    logfile = "/var/log/auth.log"
        with open(logfile, "r", encoding="utf-8") as f:
            for line in f:
                if " from " in line:
                    try:
                        dataDaLiñaDoLog = datetime.strptime(line[:10], "%Y-%m-%d").date()
                        if dataUltimoProceso < dataDaLiñaDoLog <= dataDeOnte:
                            for token in line.split():
                                try:
                                    # token = token.strip(",:;[]()")
                                    ipNaLiña = str(ipaddress.ip_address(token))
                                    if ipNaLiña:
                                        atopada = self.search([('ip', '=', ipNaLiña)], limit=1)
                                        if atopada:
                                            atopada.intentosDeAcceso += 1
                                        else:
                                            meuCountry = 'non atopado'
                                            meuContinent = 'non atopado'
                                            try:
                                                ipGeoLocalizada = self.consultaNaWebIpinfo(ipNaLiña) or {}
                                                if ipGeoLocalizada:
                                                    meuCountry = ipGeoLocalizada.get('country', meuCountry)
                                                    meuContinent = ipGeoLocalizada.get('continent', meuContinent)
                                            except Exception:
                                                pass
                                            self.create({'ip': ipNaLiña, 'intentosDeAcceso': 1, 'pais': meuCountry,
                                                         'continente': meuContinent})
                                            miñasUtilidades.rexistra_log(
                                                miñasUtilidades.convirte_data_hora_de_utc_a_timezone_do_usuario(
                                                    fields.Datetime.now(),
                                                    self.env.user.tz or 'UTC').strftime("%Y/%m/%d, %H:%M:%S"),
                                                miñasUtilidades.cadeaTextoSegunPlataforma(rutaWindowsParaLogDeSaida,
                                                                                          rutaGNULinuxParaLogDeSaida),
                                                "logIPs.log",
                                                " Alta Ip: " + str(ipNaLiña))
                                except ValueError:
                                    continue
                    except ValueError:
                        continue  # Liñas sen data
        self.env['ir.config_parameter'].sudo().set_param('logweb.dataUltimoProcesoAuthLog', dataDeOnte)

    # temos que dar permiso de lectura ao ficheiro /var/log/auth.log "chmod 644 /var/log/auth.log"
    # temos que gravar manualmente en ir.config_parameter un rexistro 'logweb.tokenParaIpinfo' co token que temos de IPinfo
    # temos que ter permiso de escritura na ruta para o LogDeSaida