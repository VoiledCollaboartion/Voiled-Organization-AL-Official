"use client"

import { Button } from "antd";
import axios from "axios";
import { Fragment, useEffect, useState } from "react";

const Profile = ({ params }) => {

    const [info, setInfo] = useState(null);

    useEffect(() => {
        axios.get(`http://localhost:5000/v1/developers/${params.id}`)
            .then(res => {
                setInfo(res.data);
            })
            .catch(err => {
                console.log(err);
            })
    }, [])

    const handleVerify = () => {
        const payload = {
            ownerId: info.user.id,
            receiverId: info.user.id
        }

        console.log(payload);
        

        axios.post(`http://localhost:5000/v1/developers/verify/send`, payload)
            .then(res => {
                console.log(res.data);
            })
            .catch(err => {
                console.log(err);
            })
    }

    return (
        <div className="w-full h-screen flex flex-col items-center p-6 justify-center">
            {
                info && (
                    <Fragment>
                        <h1 className="text-[40px] font-black">{info.user.name}</h1>
                        <h1 className="text-[40px] font-black">{info.user.email}</h1>
                        <p className="text-[16px] font-black">{info.summary}</p>
                        <Button className="mt-4 px-6" type="primary" onClick={handleVerify}>Verify</Button>
                    </Fragment>
                )
        }
        </div>
    )
}

export default Profile;