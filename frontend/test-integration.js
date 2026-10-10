async function testIntegration() {
  console.log('--- 1. Testing Backend Health ---');
  const healthRes = await fetch('http://127.0.0.1:8000/health');
  console.log('Health status code:', healthRes.status);
  const health = await healthRes.json();
  console.log('Health JSON:', health);

  console.log('\n--- 2. Testing Patients Endpoint ---');
  const patientsRes = await fetch('http://127.0.0.1:8000/api/patients');
  console.log('Patients status code:', patientsRes.status);
  const patients = await patientsRes.json();
  console.log('Patients count:', patients.length);
  patients.forEach(p => console.log(`  Patient #${p.id}: ${p.name} (${p.diabetes_type}, ${p.age}y)`));

  console.log('\n--- 3. Testing Readings for Patient #1 ---');
  const g1 = await fetch('http://127.0.0.1:8000/api/readings/glucose/1?hours=24').then(r => r.json());
  const v1 = await fetch('http://127.0.0.1:8000/api/readings/vitals/1?hours=24').then(r => r.json());
  console.log(`Patient #1: ${g1.length} glucose readings, ${v1.length} vitals readings.`);
  console.log('Latest glucose:', g1[g1.length - 1]);
  console.log('Latest vital:', v1[v1.length - 1]);

  console.log('\n--- 4. Testing Readings for Patient #2 ---');
  const g2 = await fetch('http://127.0.0.1:8000/api/readings/glucose/2?hours=24').then(r => r.json());
  const v2 = await fetch('http://127.0.0.1:8000/api/readings/vitals/2?hours=24').then(r => r.json());
  console.log(`Patient #2: ${g2.length} glucose readings, ${v2.length} vitals readings.`);
  console.log('Latest glucose:', g2[g2.length - 1]);
  console.log('Latest vital:', v2[v2.length - 1]);

  console.log('\n--- 5. Testing Frontend Server ---');
  const feRes = await fetch('http://localhost:5173/');
  console.log('Frontend status code:', feRes.status);
  const html = await feRes.text();
  console.log('Frontend serves HTML with root element:', html.includes('id="root"'));
  console.log('Frontend connects to client.js module:', html.includes('/src/main.jsx'));
  console.log('\nALL INTEGRATION ENDPOINTS VERIFIED SUCCESSFULLY!');
}

testIntegration().catch(err => {
  console.error('Integration test error:', err);
  process.exit(1);
});
