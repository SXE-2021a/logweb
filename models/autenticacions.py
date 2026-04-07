# -*- coding: utf-8 -*-

from odoo import models, fields, api
from pygments.lexer import default

from . import miñasUtilidades
import ipaddress
import requests
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import shutil
import os



class autenticacions(models.Model):
    _name = 'logweb.autenticacions'
    _description = 'autenticacions en GNU/Linux'
    _order = "continente,pais,ip asc"

    continente = fields.Char(required=True, size=25, string="Continente")
    pais = fields.Char(required=True, size=25, string="País")
    ip = fields.Char(required=True, size=15, string="IP")
    intentosDeAcceso = fields.Integer(required=True, string="Intentos de Acceso")
    cantidade = fields.Char(compute="_cantidade",size=15, store=True)

    @api.depends('intentosDeAcceso')
    def _cantidade(self):
        for rexistro in self:
            if rexistro.intentosDeAcceso > 500:
                rexistro.cantidade = "Máis de 500"
            elif rexistro.intentosDeAcceso > 99:
                rexistro.cantidade = "Entre 500 e 100"
            else:
                rexistro.cantidade = "Menos de 100"

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
        rutaWindowsParaLogs = 'c:\\users\\antonio\\logs'
        rutaGNULinuxParaLogs = '/home/antonio/logs'
        dataInicialUltimoProceso = '2000-01-01'
        dataUltimoProceso = fields.Date.from_string(self.env['ir.config_parameter'].sudo().get_param('logweb.dataUltimoProcesoAuthLog',
                                                             dataInicialUltimoProceso))
        dataDeOnte = fields.Date.today() - relativedelta(days=1)
        # Copiamos ao noso directorio o ficherio de log que queremos procesar
        #logfile = "/home/antonio/PycharmProjects/logweb/static/auth.log"
        logfile = "/var/log/auth.log"
        logAimportar = os.path.join(miñasUtilidades.cadeaTextoSegunPlataforma(rutaWindowsParaLogs,rutaGNULinuxParaLogs), 'logAImportar.txt')
        shutil.copy2(logfile,logAimportar)
        ######################################################################
        with open(logAimportar, "r", encoding="utf-8") as f:
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
                                                miñasUtilidades.cadeaTextoSegunPlataforma(rutaWindowsParaLogs,
                                                                                          rutaGNULinuxParaLogs),
                                                "logIPsImportadas.log",
                                                " Alta Ip: " + str(ipNaLiña))
                                except ValueError:
                                    continue
                    except ValueError:
                        continue  # Liñas sen data
        self.env['ir.config_parameter'].sudo().set_param('logweb.dataUltimoProcesoAuthLog', dataDeOnte)

    def email_ranking(self):
        usuario_que_executa_o_metodo_que_e_o_definido_no_xml = self.env.user
        usuario_administrador = self.env['res.partner'].search([('id', '=', 3)])[0]
        agora = miñasUtilidades.convirte_data_hora_de_utc_a_timezone_do_usuario(fields.Datetime.now(),usuario_administrador.tz)
        resultadoSUM = self.env['logweb.autenticacions'].read_group(domain=[],fields=['intentosDeAcceso:sum'],groupby=[])
        if resultadoSUM:
           total_intentosDeAcceso = resultadoSUM[0]['intentosDeAcceso']
        else:
           total_intentosDeAcceso = 0
        resultadoCOUNT = self.env['logweb.autenticacions'].read_group(domain=[], fields=['ip:count'], groupby=[])
        if resultadoCOUNT:
           total_IPs = resultadoCOUNT[0]['ip']
        else:
            total_IPs = 0
        as_5_IPs = self.env['logweb.autenticacions'].search([], order='intentosDeAcceso desc', limit=5)
        if as_5_IPs:
            listado = "<br/>"
            for rexistro in as_5_IPs:
                listado = listado + "<br/>" + "[ IP: " + str(rexistro.ip) + " ][ Intentos de Acceso: " + str(rexistro.intentosDeAcceso) + " ][ Continente: " + str(rexistro.continente) + " ][ Pais: " + str(rexistro.pais) +" ]"
            mail_reply_to = usuario_que_executa_o_metodo_que_e_o_definido_no_xml.partner_id.email  # odoobot@example.com
            mail_para = usuario_administrador.email  # o enderezo email de destino
            mail_valores = {
                'subject': "Ranking de intentos de acceso neste momento %s na compañía %s" % (agora, self.env.company.name),
                'author_id': usuario_que_executa_o_metodo_que_e_o_definido_no_xml.id,
                'email_from': mail_reply_to,
                'email_to': mail_para,
                'message_type': 'email',
                'body_html': "Neste momento %s temos %s IPs cun total de %s intentos de acceso  %s" % (agora,total_IPs,total_intentosDeAcceso, str(listado)),
            }
            mail_id = self.env['mail.mail'].create(mail_valores)
            mail_id.send()
    # Temos que ter permiso de lectura no ficheiro /var/log/auth.log  O mellor é meter ao usuario odoo no grupo adm (e así terá  permisos de lectura sobre os arquivos de log) usermod -aG adm odoo
    # temos que gravar manualmente en ir.config_parameter un rexistro 'logweb.tokenParaIpinfo' co token que temos de IPinfo
    # temos que ter permiso de escritura na ruta para o LogDeSaida