import mongoose from "mongoose";

const Schema = mongoose.Schema;

const userSchema = new Schema({
    u_name: {
        type: String,
        require: true
    },
    u_username: {
        type: String,
        unique: true,
        require: true
    },
    u_password: {
        type: String,
        require: true
    },
    u_email: {
        type: String,
        unique: true,
        require: true
    },
    u_avatar: {
        type: String
    }
})

const User = mongoose.model("user", userSchema);

export default User;