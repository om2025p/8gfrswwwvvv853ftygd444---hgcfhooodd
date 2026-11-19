const DEMO = {
  g1:{"id":"g1","name":"مظفر رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"کشاورز و باغدار","relation":"پدربزرگ پدری","birthplace":"گلبهار","isAlive":false,"birthDate":"1288/2/10","deathDate":"1355/5/2","location":"","grave":"گلبهار","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"بنیان‌گذار خاندان. باغ انگور را با دست خودش ساخت و ۴۰ سال آب داد.","parents":[],"spouses":["g2"],"children":["p1","p3","a7"],"maternalGrandparents":[],"paternalGrandparents":[]},
  g2:{"id":"g2","name":"زهرا کاظمی","gender":"female","hasPhoto":false,"photoData":"","job":"خانه‌دار","relation":"مادربزرگ پدری","birthplace":"نیشابور","isAlive":false,"birthDate":"1296/3/20","deathDate":"1370/9/14","location":"","grave":"گلبهار","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"آش رشته‌اش هنوز ضرب‌المثل خانواده است.","parents":[],"spouses":["g1"],"children":["p1","p3","a7"],"maternalGrandparents":[],"paternalGrandparents":[]},
  g3:{"id":"g3","name":"حسن موسوی","gender":"male","hasPhoto":false,"photoData":"","job":"آهنگر","relation":"پدربزرگ مادری","birthplace":"سبزوار","isAlive":false,"birthDate":"1292/7/1","deathDate":"1368/2/9","location":"","grave":"سبزوار","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"کارگاه آهنگری در بازار سبزوار داشت.","parents":[],"spouses":["g4"],"children":["p2","p4","a8"],"maternalGrandparents":[],"paternalGrandparents":[]},
  g4:{"id":"g4","name":"فاطمه صادقی","gender":"female","hasPhoto":false,"photoData":"","job":"قالی‌باف","relation":"مادربزرگ مادری","birthplace":"سبزوار","isAlive":true,"birthDate":"1302/11/5","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"۹۳ ساله و هنوز هر روز صبح چای می‌دهد.","parents":[],"spouses":["g3"],"children":["p2","p4","a8"],"maternalGrandparents":[],"paternalGrandparents":[]},
  g5:{"id":"g5","name":"ابراهیم رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"راننده کامیون","relation":"عموی پدربزرگ","birthplace":"گلبهار","isAlive":false,"birthDate":"1294/5/12","deathDate":"1345/8/3","location":"","grave":"گلبهار","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"برادر مظفر. مسیر گلبهار–مشهد را ۲۰ سال رانندگی کرد.","parents":[],"spouses":["g6"],"children":["u1"],"maternalGrandparents":[],"paternalGrandparents":[]},
  g6:{"id":"g6","name":"رقیّه نوری","gender":"female","hasPhoto":false,"photoData":"","job":"خانه‌دار","relation":"همسر عموی پدربزرگ","birthplace":"گلبهار","isAlive":false,"birthDate":"1300/1/8","deathDate":"1378/4/20","location":"","grave":"گلبهار","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"","parents":[],"spouses":["g5"],"children":["u1"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p1:{"id":"p1","name":"رحیم رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"مهندس عمران","relation":"پدر","birthplace":"گلبهار","isAlive":true,"birthDate":"1325/4/12","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":4,"bio":"پل‌های زیادی در جاده مشهد–نیشابور ساخته.","parents":["g1","g2"],"spouses":["p2"],"children":["m1","m2","m3","m4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p2:{"id":"p2","name":"مریم موسوی","gender":"female","hasPhoto":false,"photoData":"","job":"دبیر ریاضی","relation":"مادر","birthplace":"سبزوار","isAlive":true,"birthDate":"1328/8/3","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":4,"bio":"۳۲ سال ریاضی درس داده.","parents":["g3","g4"],"spouses":["p1"],"children":["m1","m2","m3","m4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p3:{"id":"p3","name":"کریم رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"معلم ادبیات","relation":"عمو","birthplace":"گلبهار","isAlive":true,"birthDate":"1322/9/5","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"برادر بزرگ‌تر پدر.","parents":["g1","g2"],"spouses":["p5"],"children":["c4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p5:{"id":"p5","name":"شهناز بهرامی","gender":"female","hasPhoto":false,"photoData":"","job":"پرستار","relation":"زنِ عمو","birthplace":"تهران","isAlive":true,"birthDate":"1329/2/17","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"","parents":[],"spouses":["p3"],"children":["c4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  a7:{"id":"a7","name":"فاطمه رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"خیاط","relation":"عمه","birthplace":"گلبهار","isAlive":true,"birthDate":"1330/4/18","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"خواهر پدر. با داییِ شما ازدواج کرد — ازدواج بین دو خانواده.","parents":["g1","g2"],"spouses":["a8"],"children":["c12"],"maternalGrandparents":[],"paternalGrandparents":[]},
  a8:{"id":"a8","name":"رضا موسوی","gender":"male","hasPhoto":false,"photoData":"","job":"زرگر","relation":"دایی","birthplace":"سبزوار","isAlive":true,"birthDate":"1327/11/2","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"برادر مادر. زرگری در بازار رضا مشهد.","parents":["g3","g4"],"spouses":["a7"],"children":["c12"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p4:{"id":"p4","name":"زینب موسوی","gender":"female","hasPhoto":false,"photoData":"","job":"خیاط","relation":"خاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1324/6/22","deathDate":"","location":"سبزوار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"خواهر مادر. لباس عروسی خیلی‌ها را دوخته.","parents":["g3","g4"],"spouses":["p6"],"children":["c5","c6"],"maternalGrandparents":[],"paternalGrandparents":[]},
  p6:{"id":"p6","name":"جواد صابری","gender":"male","hasPhoto":false,"photoData":"","job":"بقال","relation":"شوهرِ خاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1320/12/3","deathDate":"","location":"سبزوار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"","parents":[],"spouses":["p4"],"children":["c5","c6"],"maternalGrandparents":[],"paternalGrandparents":[]},
  m1:{"id":"m1","name":"علی رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"برنامه‌نویس","relation":"خودِ شما","birthplace":"مشهد","isAlive":true,"birthDate":"1352/2/18","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"در تهران نرم‌افزار می‌نویسد. عاشق کوه و قهوه.","parents":["p1","p2"],"spouses":["s1"],"children":["c1","c2"],"maternalGrandparents":[],"paternalGrandparents":[]},
  s1:{"id":"s1","name":"نگار احمدی","gender":"female","hasPhoto":false,"photoData":"","job":"معمار","relation":"همسر","birthplace":"تهران","isAlive":true,"birthDate":"1354/6/22","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"معمار داخلی.","parents":[],"spouses":["m1"],"children":["c1","c2"],"maternalGrandparents":[],"paternalGrandparents":[]},
  m2:{"id":"m2","name":"سارا رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"پزشک اطفال","relation":"خواهر","birthplace":"مشهد","isAlive":true,"birthDate":"1356/9/9","deathDate":"","location":"شیراز","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"متخصص اطفال در شیراز.","parents":["p1","p2"],"spouses":[],"children":["c3"],"maternalGrandparents":[],"paternalGrandparents":[]},
  m3:{"id":"m3","name":"مجید رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"مهندس برق","relation":"برادر","birthplace":"مشهد","isAlive":true,"birthDate":"1360/1/27","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"در شرکت توزیع برق مشهد.","parents":["p1","p2"],"spouses":["s2"],"children":["c7"],"maternalGrandparents":[],"paternalGrandparents":[]},
  s2:{"id":"s2","name":"الهام رستمی","gender":"female","hasPhoto":false,"photoData":"","job":"حسابدار","relation":"زنِ برادر","birthplace":"مشهد","isAlive":true,"birthDate":"1362/4/11","deathDate":"","location":"مشهد","grave":"","isMarried":true,"spousesCount":1,"childrenCount":1,"bio":"","parents":[],"spouses":["m3"],"children":["c7"],"maternalGrandparents":[],"paternalGrandparents":[]},
  m4:{"id":"m4","name":"مینا رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"گرافیست","relation":"خواهر","birthplace":"مشهد","isAlive":true,"birthDate":"1358/11/30","deathDate":"","location":"اصفهان","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"طراح گرافیک در اصفهان.","parents":["p1","p2"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  c4:{"id":"c4","name":"امیرحسین رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"وکیل","relation":"پسرعمو","birthplace":"تهران","isAlive":true,"birthDate":"1355/3/14","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"وکیل دادگستری. با دخترخالهٔ شما ازدواج کرد.","parents":["p3","p5"],"spouses":["c5"],"children":["c13","c14"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c5:{"id":"c5","name":"حمیده صابری","gender":"female","hasPhoto":false,"photoData":"","job":"آرایشگر","relation":"دخترخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1350/8/8","deathDate":"","location":"تهران","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"سالن زیبایی دارد. ازدواج بین دو خانواده.","parents":["p4","p6"],"spouses":["c4"],"children":["c13","c14"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c6:{"id":"c6","name":"سعید صابری","gender":"male","hasPhoto":false,"photoData":"","job":"مکانیک","relation":"پسرخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1353/5/25","deathDate":"","location":"سبزوار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"تعمیرگاه خودرو در سبزوار.","parents":["p4","p6"],"spouses":["s4"],"children":["c9","c10","c11"],"maternalGrandparents":[],"paternalGrandparents":[]},
  s4:{"id":"s4","name":"پریسا اکبری","gender":"female","hasPhoto":false,"photoData":"","job":"خانه‌دار","relation":"زنِ پسرخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1356/10/2","deathDate":"","location":"سبزوار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":3,"bio":"","parents":[],"spouses":["c6"],"children":["c9","c10","c11"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c12:{"id":"c12","name":"مهدی موسوی","gender":"male","hasPhoto":false,"photoData":"","job":"عکاس","relation":"پسرعمه و دایی","birthplace":"مشهد","isAlive":true,"birthDate":"1357/8/23","deathDate":"","location":"مشهد","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"فرزند ازدواج عمه و دایی. عکاس خبری.","parents":["a7","a8"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  c1:{"id":"c1","name":"آوا رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"دانشجوی پزشکی","relation":"دختر","birthplace":"تهران","isAlive":true,"birthDate":"1380/5/4","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":2,"bio":"دانشجوی سال چهارم پزشکی.","parents":["m1","s1"],"spouses":[],"children":["n1","n2"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c2:{"id":"c2","name":"آرش رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسر","birthplace":"تهران","isAlive":true,"birthDate":"1383/10/15","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"تیم رباتیک مدرسه.","parents":["m1","s1"],"spouses":[],"children":["n6"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c3:{"id":"c3","name":"هانا رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"دخترِ خواهر","birthplace":"شیراز","isAlive":true,"birthDate":"1385/12/1","deathDate":"","location":"شیراز","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"","parents":["m2"],"spouses":[],"children":["n3"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c7:{"id":"c7","name":"رادین رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسرِ برادر","birthplace":"مشهد","isAlive":true,"birthDate":"1390/3/20","deathDate":"","location":"مشهد","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"","parents":["m3","s2"],"spouses":[],"children":["n4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c13:{"id":"c13","name":"آرمین رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسرِ پسرعمو","birthplace":"تهران","isAlive":true,"birthDate":"1384/6/9","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c4","c5"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  c14:{"id":"c14","name":"آرمان رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسرِ پسرعمو","birthplace":"تهران","isAlive":true,"birthDate":"1387/2/11","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c4","c5"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  c9:{"id":"c9","name":"مهسا صابری","gender":"female","hasPhoto":false,"photoData":"","job":"دانشجوی حقوق","relation":"دخترِ پسرخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1378/2/14","deathDate":"","location":"سبزوار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"","parents":["c6","s4"],"spouses":[],"children":["n5"],"maternalGrandparents":[],"paternalGrandparents":[]},
  c10:{"id":"c10","name":"کیان صابری","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسرِ پسرخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1388/9/7","deathDate":"","location":"سبزوار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c6","s4"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  c11:{"id":"c11","name":"نیلوفر صابری","gender":"female","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"دخترِ پسرخاله","birthplace":"سبزوار","isAlive":true,"birthDate":"1392/1/25","deathDate":"","location":"سبزوار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c6","s4"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n1:{"id":"n1","name":"بردیا رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"تهران","isAlive":true,"birthDate":"1401/7/12","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"تازه راه افتاده.","parents":["c1"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n2:{"id":"n2","name":"روژان رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"تهران","isAlive":true,"birthDate":"1404/2/3","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c1"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n3:{"id":"n3","name":"سام رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"شیراز","isAlive":true,"birthDate":"1403/5/19","deathDate":"","location":"شیراز","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c3"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n4:{"id":"n4","name":"آیلین رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"مشهد","isAlive":true,"birthDate":"1402/11/8","deathDate":"","location":"مشهد","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c7"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n5:{"id":"n5","name":"آوا صابری","gender":"female","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"سبزوار","isAlive":true,"birthDate":"1402/3/6","deathDate":"","location":"سبزوار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c9"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  n6:{"id":"n6","name":"تیام رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"—","relation":"نوه","birthplace":"تهران","isAlive":true,"birthDate":"1405/1/22","deathDate":"","location":"تهران","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["c2"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  u1:{"id":"u1","name":"غلامرضا رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"راننده تاکسی","relation":"پسرعموی پدربزرگ","birthplace":"گلبهار","isAlive":true,"birthDate":"1327/3/3","deathDate":"","location":"گلبهار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"در گلبهار تاکسی دارد.","parents":["g5","g6"],"spouses":["u2"],"children":["u3","u4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  u2:{"id":"u2","name":"طاهره رحیمی","gender":"female","hasPhoto":false,"photoData":"","job":"خانه‌دار","relation":"همسر پسرعموی پدربزرگ","birthplace":"گلبهار","isAlive":true,"birthDate":"1330/7/27","deathDate":"","location":"گلبهار","grave":"","isMarried":true,"spousesCount":1,"childrenCount":2,"bio":"","parents":[],"spouses":["u1"],"children":["u3","u4"],"maternalGrandparents":[],"paternalGrandparents":[]},
  u3:{"id":"u3","name":"بهنام رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"باغدار","relation":"پسرعموی پدر","birthplace":"گلبهار","isAlive":true,"birthDate":"1354/1/16","deathDate":"","location":"گلبهار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":1,"bio":"","parents":["u1","u2"],"spouses":[],"children":["u5"],"maternalGrandparents":[],"paternalGrandparents":[]},
  u4:{"id":"u4","name":"سمیرا رضایی","gender":"female","hasPhoto":false,"photoData":"","job":"پرستار","relation":"دخترعموی پدر","birthplace":"نیشابور","isAlive":true,"birthDate":"1358/4/4","deathDate":"","location":"نیشابور","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["u1","u2"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]},
  u5:{"id":"u5","name":"پویا رضایی","gender":"male","hasPhoto":false,"photoData":"","job":"دانش‌آموز","relation":"پسرعموی دوم","birthplace":"گلبهار","isAlive":true,"birthDate":"1389/8/21","deathDate":"","location":"گلبهار","grave":"","isMarried":false,"spousesCount":1,"childrenCount":0,"bio":"","parents":["u3"],"spouses":[],"children":[],"maternalGrandparents":[],"paternalGrandparents":[]}
};

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const initial = n => (n || '؟').trim().charAt(0);
const yearOf = d => { if (!d) return 0; if (typeof d === 'string') { const y = parseInt(d.split('/')[0], 10); return isNaN(y) ? 0 : y; } return d.y || 0; };
const jy = d => { if (!d) return '—'; if (typeof d === 'string') { const p = d.split('/'); return p[0] ? p[0] : '—'; } return d.y ? String(d.y) : '—'; };
const isDead = m => m.isAlive === false;
const lifeSpan = m => `${jy(m.birthDate)}${isDead(m) ? '–' + jy(m.deathDate) : ''}`;

function ancestorSet(id, maxUp = 8) {
  const out = new Set();
  let frontier = [id];
  for (let d = 0; d < maxUp && frontier.length; d++) {
    const next = [];
    frontier.forEach(n => {
      const m = M[n];
      if (!m) return;
      (m.parents || []).forEach(pa => {
        if (M[pa] && !out.has(pa)) { out.add(pa); next.push(pa); }
      });
    });
    frontier = next;
  }
  return out;
}

/* Which side: 'p' paternal, 'm' maternal, 'self' the root itself.
   A person belongs to a side when any of their ancestors is an ancestor
   (or the parent) of the root on that side. Spouses marrying in and
   descendants with no recorded parents inherit the side of their
   spouse or child — otherwise they all collapse into one panel. */
function sideOf(id, root, seen) {
  if (id === root) return 'self';
  if (!M[id] || !M[root]) return 'p';
  seen = seen || new Set();
  if (seen.has(id)) return 'p';
  seen.add(id);

  const R = M[root];
  const father = (R.parents || []).find(x => M[x] && M[x].gender !== 'female');
  const mother = (R.parents || []).find(x => M[x] && M[x].gender === 'female');

  if (id === father) return 'p';
  if (id === mother) return 'm';

  const pSide = new Set(), mSide = new Set();
  if (father) { pSide.add(father); ancestorSet(father).forEach(x => pSide.add(x)); }
  if (mother) { mSide.add(mother); ancestorSet(mother).forEach(x => mSide.add(x)); }

  const anc = ancestorSet(id);
  let inP = false, inM = false;
  anc.forEach(a => {
    if (pSide.has(a)) inP = true;
    if (mSide.has(a)) inM = true;
  });
  if (inP && !inM) return 'p';
  if (inM && !inP) return 'm';
  if (inP && inM) return 'p';

  /* no ancestors at all → borrow the side from the spouse, then the children */
  for (const sid of (M[id].spouses || [])) {
    if (M[sid] && sid !== root) {
      const sd = sideOf(sid, root, seen);
      if (sd === 'p' || sd === 'm') return sd;
    }
  }
  for (const cid of (M[id].children || [])) {
    if (M[cid] && cid !== root) {
      const sd = sideOf(cid, root, seen);
      if (sd === 'p' || sd === 'm') return sd;
    }
  }
  return 'p';
}

/* Persian kinship term from the root's point of view.
   Two passes, and the order matters: blood relations are resolved first,
   marriage-in relations only after. Someone can be both — e.g. a man who
   is the mother's brother AND married the father's sister is a دایی, not
   a «شوهرِ عمه». */
function kinshipOf(id, root) {
  if (id === root) return 'خودِ شما';
  const R = M[root], m = M[id];
  if (!m || !R) return '';

  const male = m.gender !== 'female';
  const rParents = (R.parents || []).filter(x => M[x]);
  const rChildren = (R.children || []).filter(x => M[x]);
  const father = rParents.find(x => M[x].gender !== 'female');
  const mother = rParents.find(x => M[x].gender === 'female');

  const parentsOf = x => (M[x] && M[x].parents || []).filter(y => M[y]);
  const kidsOf = x => (M[x] && M[x].children || []).filter(y => M[y]);
  const spousesOf = x => (M[x] && M[x].spouses || []).filter(y => M[y]);
  const shareParent = (a, b) => parentsOf(a).some(x => parentsOf(b).includes(x));

  /* ---------- 1. blood ---------- */
  if (rParents.includes(id)) return male ? 'پدر' : 'مادر';
  if (rChildren.includes(id)) return male ? 'پسر' : 'دختر';
  if ((R.spouses || []).includes(id)) return 'همسر';

  const rSibs = ids.filter(x => x !== root && M[x] && shareParent(x, root));
  if (rSibs.includes(id)) {
    const ay = yearOf(m.birthDate), ry = yearOf(R.birthDate);
    const older = ay && ry ? ay < ry : true;
    if (male) return older ? 'برادر بزرگ‌تر' : 'برادر کوچک‌تر';
    return older ? 'خواهر بزرگ‌تر' : 'خواهر کوچک‌تر';
  }

  /* uncles / aunts — blood siblings of either parent */
  for (const [par, isPaternal] of [[father, true], [mother, false]]) {
    if (!par) continue;
    const parSibs = ids.filter(x => x !== par && M[x] && shareParent(x, par));
    if (parSibs.includes(id)) {
      if (isPaternal) return male ? 'عمو' : 'عمه';
      return male ? 'دایی' : 'خاله';
    }
  }

  /* children of the root's siblings → nephews / nieces */
  for (const sib of rSibs) {
    if (kidsOf(sib).includes(id)) {
      const sibMale = M[sib].gender !== 'female';
      if (male) return sibMale ? 'برادرزاده' : 'خواهرزاده';
      return sibMale ? 'برادرزاده (دختر)' : 'خواهرزاده (دختر)';
    }
  }

  /* cousins */
  for (const [par, isPaternal] of [[father, true], [mother, false]]) {
    if (!par) continue;
    const parSibs = ids.filter(x => x !== par && M[x] && shareParent(x, par));
    const cousins = parSibs.flatMap(x => kidsOf(x));
    if (cousins.includes(id)) {
      if (isPaternal) return male ? 'پسرعمو' : 'دخترعمو';
      return male ? 'پسردایی' : 'دختردایی';
    }
    const cousins2 = cousins.flatMap(x => kidsOf(x));
    if (cousins2.includes(id)) {
      if (isPaternal) return male ? 'پسرعموزاده' : 'دخترعموزاده';
      return male ? 'پسردایی‌زاده' : 'دختردایی‌زاده';
    }
  }

  /* grandchildren and further */
  const gk = rChildren.flatMap(x => kidsOf(x));
  if (gk.includes(id)) return male ? 'نوه (پسرِ فرزند)' : 'نوه (دخترِ فرزند)';
  if (gk.flatMap(x => kidsOf(x)).includes(id)) return 'نتیجه';

  /* grandparents */
  const gp = rParents.flatMap(x => parentsOf(x));
  if (gp.includes(id)) return male ? 'پدربزرگ' : 'مادربزرگ';

  /* ---------- 2. marriage-in ---------- */
  for (const sib of rSibs) {
    if (spousesOf(sib).includes(id)) return M[sib].gender !== 'female' ? 'زنِ برادر' : 'شوهرِ خواهر';
  }
  for (const [par, isPaternal] of [[father, true], [mother, false]]) {
    if (!par) continue;
    const parSibs = ids.filter(x => x !== par && M[x] && shareParent(x, par));
    for (const sib of parSibs) {
      if (spousesOf(sib).includes(id)) {
        const sibMale = M[sib].gender !== 'female';
        if (isPaternal) return sibMale ? 'زنِ عمو' : 'شوهرِ عمه';
        return sibMale ? 'زنِ دایی' : 'شوهرِ خاله';
      }
    }
    const cousins = parSibs.flatMap(x => kidsOf(x));
    for (const cu of cousins) {
      if (spousesOf(cu).includes(id)) {
        const cuMale = M[cu].gender !== 'female';
        if (isPaternal) return cuMale ? 'زنِ پسرعمو' : 'شوهرِ دخترعمو';
        return cuMale ? 'زنِ پسردایی' : 'شوهرِ دختردایی';
      }
    }
  }
  for (const ch of rChildren) {
    if (spousesOf(ch).includes(id)) return M[ch].gender !== 'female' ? 'زنِ پسر' : 'شوهرِ دختر';
  }

  /* ---------- 3. fallback by generation gap ---------- */
  const dd = (depth[id] || 0) - (depth[root] || 0);
  const t = sideOf(id, root) === 'm' ? 'مادری' : 'پدری';
  if (dd <= -2) return 'جد ' + t;
  if (dd === -1) return 'والدِ ' + t;
  if (dd === 1) return 'فرزندِ ' + t;
  if (dd >= 2) return 'نوهٔ ' + t;
  return 'خویشاوند ' + t;
}

/* ---- bridge: the shared kinship code expects M (object) and ids (array) ---- */
const M = DEMO;
const ids = Object.keys(DEMO);
const depth = {};
function computeDepth(){
  const memo = {};
  function d(id, stack){
    if (memo[id] !== undefined) return memo[id];
    if (stack.has(id)) return 0;
    stack.add(id);
    const ps = (M[id].parents || []).filter(p => M[p]);
    const v = ps.length ? 1 + Math.max(...ps.map(p => d(p, stack))) : 0;
    stack.delete(id); memo[id] = v; return v;
  }
  ids.forEach(id => d(id, new Set()));
  const hasParents = id => (M[id].parents || []).some(p => M[p]);
  for (let pass = 0; pass < 6; pass++) {
    let changed = false;
    ids.forEach(id => {
      if (hasParents(id)) return;
      const fromSpouse = (M[id].spouses || []).filter(x => M[x] && memo[x] !== undefined).map(x => memo[x]);
      if (fromSpouse.length) {
        const v = Math.min(...fromSpouse);
        if (memo[id] !== v) { memo[id] = v; changed = true; }
        return;
      }
      const kids = (M[id].children || []).filter(x => M[x] && memo[x] > 0).map(x => memo[x]);
      if (kids.length) {
        const v = Math.max(0, Math.min(...kids) - 1);
        if (memo[id] !== v) { memo[id] = v; changed = true; }
      }
    });
    if (!changed) break;
  }
  ids.forEach(id => depth[id] = memo[id]);
}
computeDepth();
