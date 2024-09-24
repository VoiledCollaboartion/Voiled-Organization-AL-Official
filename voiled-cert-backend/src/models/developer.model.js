const mongoose = require("mongoose");
const { toJSON, paginate } = require('./plugins');

const developerSchema = new mongoose.Schema({
    user: {
        type: mongoose.SchemaTypes.ObjectId,
        required: true,
        ref: "User",
        unique: true
    },
    birthday: {
        type: Date,
        required: true
    },
    address: {
        type: String,
        required: true
    },
    summary: {
        type: String,
        required: true,
    },
    education: [
        {
            school_name: {
                type: String,
                requried: true   
            },
            country: {
                type: String,
                required: true
            },
            city: {
                type: String,
                required: true
            },
            start: {
                type: String,
                required: true
            },
            end: {
                type: String,
                required: true
            },
            subject: {
                type: String,
                required: true
            }
        }
    ],
    experience: [
        {
            company_name: {
                type: String,
                requried: true
            },
            country: {
                type: String,
                required: true
            },
            city: {
                type: String,
                required: true
            },
            start: {
                type: String,
                required: true
            },
            end: {
                type: String,
                required: true
            },
            content: {
                type: String,
                required: true
            },
            job: {
                type: String,
                required: true
            }
        }
    ]
})

developerSchema.plugin(toJSON);
developerSchema.plugin(paginate);

const Developer = mongoose.model('Developer', developerSchema);

module.exports = Developer;