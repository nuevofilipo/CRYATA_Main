const cron = require('node-cron');
const { exec } = require('child_process');

// Define the cron schedule
cron.schedule('*/30 * * * * *', () => {
    console.log('Running Python script at:', new Date().toISOString());

    // Execute the Python script as a child process
    exec('python test.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`Python script encountered an error: ${stderr}`);
            return;
        }
        console.log(`Python script output: ${stdout}`);
    });
});