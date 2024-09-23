import QRCode                from "qrcode"; 
import bcrypt                from "bcryptjs";
import path                  from "path";
import User                  from "../models/user";
import makeResponse          from "../utils/response";
import net                   from "net";
import nodemailer            from 'nodemailer';
import { decryptWithSecret, encryptWithSecret } from "../utils/encrypt";
import key from "../config/key";
import decodeQRCode from "../utils/decodeQRCode";

export const registerFreelancer = (req, res) => {
    const newFreelancer = new User(req.body);
    User.findOne({ u_username: req.body.u_username })
    .then(user => {
        if (user) {
            return res.send(makeResponse(405, null, "Username already taken."));
        } else {
            bcrypt.genSalt(10, (err, salt) => {
                if (err) return res.send(makeResponse(406, err));
        
                bcrypt.hash(req.body.u_password, salt, (err, hash) => {
                    newFreelancer.u_password = hash;
        
                    newFreelancer
                        .save()
                        .then(() => {
                            return res.send(200, null);
                        })
                        .catch(err => {
                            return res.send(makeResponse(405, err));
                    })
                })
            })
        }
    })
    .catch(err => {
        return res.send(makeResponse(405, err));
    })
}

export const generateQRCode = (req, res) => {
    const { _id } = req.body;

    User
        .findOne({ _id: _id })
        .then(user => {

            const qrcodeSaveUrl = path.join(__dirname, "../uploads/qrcode", `${_id}.png`);
            
            let encryptedData = encryptWithSecret(user.u_email, key[process.env.NODE_ENV].secret);

            QRCode.toFile(qrcodeSaveUrl, encryptedData, (err) => {
                if (err) return res.send(makeResponse(405, err));
                return res.send(makeResponse(200));
            })
        })
}

export const verifyWithQRCode = (req, res) => {
    const { _id } = req.body;

    const qrcodeUrl = path.join(__dirname, "../uploads/qrcode", `${_id}.png`);

    decodeQRCode(qrcodeUrl)
    .then(result => { 
        let decoded = decryptWithSecret(result, key[process.env.NODE_ENV].secret);
        console.log(decoded);

        const transporter = nodemailer.createTransport({
            host: "smtp-mail.outlook.com", // hostname
            secureConnection: false, // TLS requires secureConnection to be false
            port: 587, // port for secure SMTP
            auth: {
                user: "cupidara@outlook.com",
                pass: "=============",
            },
            debug: true
        });


        transporter.sendMail({//what d
            from: 'cupidara@outlook.com', // sender address
            to: "happymorning505@proton.me", // list of receivers
            subject: "Hello ✔", // Subject line
            text: "Hello world?", // plain text body
            html: "<b>Hello world?</b>", // html body
        }).then(() => {
            console.log("success");
            res.send("success"); // maybe changin my psw of proton? lol. what do you want?
            
        }).catch(err => {
            console.log(err);
            res.send("error");
        })
    })
}

