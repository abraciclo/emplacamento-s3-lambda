// app.js
const { exec } = require('child_process');

// Substitua 'seu_script.sh' pelo caminho do seu script
exec('sh ./core_script.sh', (error, stdout, stderr) => {
    if (error) {
        console.error(`Erro: ${error.message}`);
        return;
    }
    if (stderr) {
        console.error(`Stderr: ${stderr}`);
        return;
    }
    console.log(`Resultado:\n${stdout}`);
});


