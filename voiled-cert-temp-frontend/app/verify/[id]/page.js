"use client"

import { Button, Input } from "antd";
import axios from "axios";
import { useState } from "react";

const Verify = ({ params }) => {

    const [code, setCode] = useState("");

    const handleSubmit = () => {
        const payload = {
            ownerId: params.id,
            token: code
        }

        console.log(payload);
        

        axios.post(`http://localhost:5000/v1/developers/verify/compare?ownerId=${params.id}`, payload)
            .then(res => {
                console.log(res.data);
            })
            .catch((err) => {
                console.log(err);
            })
    }

    return (
        <div className="w-full h-screen flex flex-col items-center justify-center">
            <Input onChange={e => setCode(e.target.value)} value={code} className="w-96"/>
            <Button className="mt-4" type="primary" onClick={handleSubmit}>Submit Code</Button>
        </div>
    )
}

export default Verify;