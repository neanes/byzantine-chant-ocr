import { spawn } from 'child_process';

export async function launchOcr(
  scriptPath: string,
  imagePath: string,
  outputPath: string,
  splitLeftRight: boolean = false,
) {
  const args = [scriptPath, imagePath, '-o', outputPath];

  if (splitLeftRight) {
    args.push('--split-lr');
  }

  const process = spawn('python', args);

  //let output = '';
  //let error = '';

  // process.stdout.on('data', function (data: string) {
  //   output += data;
  // });

  process.stderr.on('data', function (data) {
    //error += data;
    console.log(data.toString());
  });

  await new Promise((resolve) => {
    process.on('close', resolve);
  });

  //console.log(error);

  //return output;
}
