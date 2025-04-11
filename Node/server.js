const express = require('express');
const cors = require("cors");
const bodyParser = require('body-parser');
const { S3Client, ListObjectsV2Command, GetObjectCommand, HeadBucketCommand } = require('@aws-sdk/client-s3');
const archiver = require('archiver');
const stream = require('stream');
const app = express();
const port = 5000;

app.use(cors());
app.use(express.json());
app.use(bodyParser.json());

app.post('/fetch-documents', async (req, res) => {
  const { accessKey, secretKey,bucketName } = req.body;
//   const bucketName = 'privatebucketnodejs';
const bucket=bucketName;
  try {
    // const region = await getBucketRegion(accessKey, secretKey, bucketName);

    const s3Client = new S3Client({
      region: "ap-south-1",
      credentials: {
        accessKeyId: accessKey,
        secretAccessKey: secretKey,
      }
    });

    const listData = await s3Client.send(new ListObjectsV2Command({ Bucket: bucket }));
    const objects = listData.Contents;

    if (!objects || objects.length === 0) {
      return res.status(404).send('No files found.');
    }

    // Set response headers for zip
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Content-Disposition', 'attachment; filename=files.zip');

    const archive = archiver('zip', { zlib: { level: 9 } });
    archive.pipe(res);

    for (let obj of objects) {
      const getObjectParams = { Bucket: bucketName, Key: obj.Key };
      const getObjectCommand = new GetObjectCommand(getObjectParams);
      const data = await s3Client.send(getObjectCommand);
      archive.append(data.Body, { name: obj.Key });
    }

    archive.finalize();
  } catch (err) {
    console.error('Failed to download and zip files:', err);
    res.status(500).json({ error: 'Error downloading and zipping S3 files.' });
  }
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
