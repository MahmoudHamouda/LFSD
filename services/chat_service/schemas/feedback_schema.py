from marshmallow import Schema, fields

class FeedbackSchema(Schema):
    id = fields.Int(dump_only=True)
    message_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    feedback = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)
