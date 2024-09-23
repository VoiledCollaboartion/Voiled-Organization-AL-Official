import mongoose from "mongoose";

import key      from "./key";

const ENV = process.env.NODE_ENV || "dev";

const connectDB = () => {
    mongoose.connect(key[ENV].dbURL)
            .then(() => {
                console.log("DB connected");
            })
            .catch((err) => {
                console.log(err);
            })
}

export default connectDB;