from odoo import api, models, _

class MergePartnerAutomatic(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    def _merge(self, src_partners, dst_partner):
       for src in src_partners:
          for c in self.env['res.company'].search([]):
             src_partner = self.env['res.partner'].search([('id','=',src)])
             if src_partner.with_company(c.id).coopcycle_bind_id and not dst_partner.with_company(c.id).coopcycle_bind_id:
               dst_partner.with_company(c.id).coopcycle_bind_id = src_partner.with_company(c.id).coopcycle_bind_id
       super(MergePartnerAutomatic, self)._merge(src_partners, dst_partner)

