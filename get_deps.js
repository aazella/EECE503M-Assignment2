const fs = require('fs');

fs.readFile('package.json', 'utf8', 
  (err, data) => {
     if (err) {
       return;
  }
  const jsonObject = JSON.parse(data);
  console.log(Object.keys(jsonObject.dependencies));
});
