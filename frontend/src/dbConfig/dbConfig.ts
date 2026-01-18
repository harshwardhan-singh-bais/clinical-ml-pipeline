import mongoose from "mongoose";

export async function connect() 
{
    try {
        mongoose.connect(process.env.MONGO_URL!); // yha exclaimation mark is used to tell typescript
        // that this variable is surely avaialble and not undefined

        const connection = mongoose.connection;

        connection.on('connected', () => {
            console.log("mongoDB connected successfully")
        })
        
        connection.on('error', (err) => {
            console.log("mongoDB connection failed")
            console.log(err)

            process.exit();
        })
    } catch (error) {
        console.log("Error connecting to database");
        console.log(error);
    }
}