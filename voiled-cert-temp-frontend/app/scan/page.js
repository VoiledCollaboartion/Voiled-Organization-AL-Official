"use client"

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, Button, notification } from 'antd';
import ImgCrop from 'antd-img-crop';
import jsQR from 'jsqr';
import axios from 'axios';

const App = () => {
    
    const [file, setFile] = useState(null);

    const [api, contextHolder] = notification.useNotification();

    const router = useRouter();

    const handleScan = () => {
        const img = new Image();
        img.src = file;
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, canvas.width, canvas.height);

            if (code) {
                api.success({
                    message: "QR Code Scanning Success.",
                    description: `This is a valid QR Code. This page will redirected soon.`
                })
                axios.post("http://localhost:5000/v1/users/info/id_by_email", { email: code.data })
                    .then(res => {
                        router.push(`/profile/${res.data}`);
                    })
                    .catch(err => {
                        console.log(err);
                    })
            } else {
                api.error({
                    message: 'QR code not found.',
                    description: "This is not a valid QR Code."
                });
            }
        };
    }

    return (
        <div className='w-full flex justify-center items-center h-screen flex-col'>
            {contextHolder}
            {
                file ?
                    <div className='w-96 h-26 relative'>
                        <img src={file} alt='QR Code' />
                        <div
                            className='absolute top-1 right-1 cursor-pointer hover:bg-black/70 rounded-full bg-black text-white w-6 h-6 text-center'
                            onClick={() => setFile(null)}
                        >
                            X
                        </div>
                    </div>
                    :
                    <ImgCrop rotationSlider>
                        <Upload
                            listType="picture-card"
                            beforeUpload={(file) => {
                                return new Promise((resolve) => {
                                    const reader = new FileReader();
                                    reader.readAsDataURL(file);
                                    reader.onload = () => {
                                        setFile(reader.result);
                                    };
                                });
                            }}
                        >
                            +
                        </Upload>
                    </ImgCrop>
            }
            <Button type="primary" disabled={!file} className='mt-4' onClick={handleScan}>Scan QR Code</Button>
        </div>
    );
};
export default App;