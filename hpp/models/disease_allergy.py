from odoo import models, fields, api

class Disease(models.Model):
    _name = "hospital.disease"
    _description = "Disease"

    name = fields.Char(string="Disease Name", required=True)
    description = fields.Text(string="Description")
    question_ids = fields.One2many('hospital.disease.question', 'disease_id', string="Related Questions")


class Allergy(models.Model):
    _name = "hospital.allergy"
    _description = "Allergy"

    name = fields.Char(string="Allergy Name", required=True)
    description = fields.Text(string="Description")
    question_ids = fields.One2many('hospital.allergy.question', 'allergy_id', string="Related Questions")


class DiseaseQuestion(models.Model):
    _name = "hospital.disease.question"
    _description = "Disease Question"

    disease_id = fields.Many2one('hospital.disease', string="Disease", required=True, ondelete='cascade')
    question = fields.Char(string="Question", required=True)
    answer = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Answer", default="no")


class PatientDiseaseQuestion(models.Model):
    _name = "hospital.patient.disease.question"
    _description = "Patient Disease Question"

    patient_id = fields.Many2one('res.partner', string="Patient", required=True, ondelete="cascade")
    question = fields.Char(string="Question", required=True, default="Default Question")
    answer = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')

    ], string="Answer", default="no")


class QuestionAnswer(models.Model):
    _name = "hospital.question.answer"
    _description = "Question Answer"

    name = fields.Char(string="Answer", required=True)
    question_id = fields.Many2one('hospital.disease.question', string="Related Question")


class AllergyQuestion(models.Model):
    _name = "hospital.allergy.question"
    _description = "Allergy Question"

    allergy_id = fields.Many2one('hospital.allergy', string="Allergy", required=True)
    question = fields.Char(string="Question", required=True)
    answer = fields.Text(string="Answer")
