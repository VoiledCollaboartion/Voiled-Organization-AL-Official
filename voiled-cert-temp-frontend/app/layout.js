import localFont from "next/font/local";

import { Divider, Menu } from "antd";
import { SolutionOutlined, ReadOutlined, HistoryOutlined, StarOutlined, GroupOutlined, IdcardOutlined } from "@ant-design/icons";

import "./globals.css";
import Link from "next/link";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata = {
  title: "Create Next App",
  description: "Generated by create next app",
};

export default function RootLayout({ children }) {
  const items = [
    {
      key: "profile",
      icon: <SolutionOutlined />,
      label: <Link href={"/resume/profile/add"}>Profile</Link>
    },
    {
      key: "education",
      icon: <ReadOutlined />,
      label: <Link href={"/resume/profile/add"}>Education</Link>
    },
    {
      key: "experience",
      icon: <HistoryOutlined />,
      label: <Link href={"/resume/profile/add"}>Experience</Link>
    },
    {
      key: "skill",
      icon: <StarOutlined />,
      label: <Link href={"/resume/profile/add"}>Skill</Link>
    },
    {
      key: "group",
      icon: <GroupOutlined />,
      label: <Link href={"/resume/profile/add"}>Freelancer</Link>
    },
    {
      key: "cert",
      icon: <IdcardOutlined />,
      label: <Link href={"/resume/profile/add"}>Certification</Link>
    },
  ]

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="flex flex-row">
          <div className="w-72 border-r">
            <h2 className="text-xl font-black text-center pt-6">Voiled</h2>
            <Divider />
            <Menu items={items} mode="inline" style={{borderRight: 'none'}}/>
          </div>
          <div className="flex-1">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
