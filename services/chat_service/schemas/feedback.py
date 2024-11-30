from marshmallow import Schema, fields


class SharedFeedbackSchema(Schema):
    message_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    feedback = fields.Str(required=True)
