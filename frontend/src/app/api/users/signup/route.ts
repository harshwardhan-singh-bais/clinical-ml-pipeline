import { connect } from "@/dbConfig/dbConfig";
import User from "@/models/userModel"
import { NextResponse, NextRequest } from "next/server";
import bcrypt from "bcryptjs";
import { sendEmail } from "@/helpers/mailer";

connect();

export async function POST(request: NextRequest) {
    try {
        const reqBody = await request.json();
        const { username, email, password } = reqBody;
        
        console.log(reqBody)

        //checking if user already exists using mongodb library functions
        const user = await User.findOne({ email })
        
        if (user) {
            return NextResponse.json({ message: "User already exists" }, { status: 400 });
        }

        //gonna hash the password using bcryptjs
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash
            (password, salt);
        
        const newUser = new User({
            username, 
            email,
            password: hashedPassword
        })

        const savedUser = await newUser.save()
        console.log("User signed up successfully:", savedUser);

        // Send email to user
        await sendEmail({
            email,
            emailType: "VERIFY",
            userId: savedUser._id
        });

        return NextResponse.json({ message: "User signed up successfully" }, { status: 201 });

    } catch (error: any) {
        return NextResponse.json({message: error.message}, {status: 500});
    }
}