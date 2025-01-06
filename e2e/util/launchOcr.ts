import { spawn } from 'child_process';

export async function launchOcr(
  scriptPath: string,
  imagePath: string,
  outputPath: string,
) {
  const process = spawn('python', [scriptPath, imagePath, '-o', outputPath]);

  //let output = '';
  //let error = '';

  // process.stdout.on('data', function (data: string) {
  //   output += data;
  // });

  //   process.stderr.on('data', function (data) {
  //     error += data;
  //   });

  await new Promise((resolve) => {
    process.on('close', resolve);
  });

  //console.log(error);

  //return output;
}
