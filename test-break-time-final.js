const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    console.log('='.repeat(50));
    console.log('TEST: Campo de 休憩時間 mejorado');
    console.log('='.repeat(50));

    console.log('\n1. Navegando a factory ID 54...');
    await page.goto('http://localhost:3010/factories/54', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log('2. Haciendo clic en Editar...');
    const editButton = await page.locator('button:has-text("編集")').first();
    await editButton.click();
    await page.waitForTimeout(2000);

    console.log('3. Buscando campo de休憩時間...');
    const breakTimeTextarea = await page.locator('textarea[name="break_time_description"]');
    await breakTimeTextarea.waitFor({ state: 'visible', timeout: 10000 });

    console.log('4. Haciendo scroll al campo...');
    await breakTimeTextarea.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);

    console.log('5. Verificando elementos mejorados...');
    
    const guideBox = await page.locator('text=📝 入力形式');
    const isVisible = await guideBox.isVisible();
    
    const placeholder = await breakTimeTextarea.getAttribute('placeholder');
    const hasCorrectPlaceholder = placeholder && placeholder.includes('①11:00');
    
    const guideParent = await guideBox.locator('..').first();
    const guideText = await guideParent.textContent();
    const hasNumbered = guideText.includes('番号付き');
    const hasShift = guideText.includes('シフト別');

    console.log('\n' + '='.repeat(50));
    console.log('RESULTADOS:');
    console.log('='.repeat(50));
    console.log('Guia azul visible:', isVisible ? 'SI' : 'NO');
    console.log('Formato numerado explicado:', hasNumbered ? 'SI' : 'NO');
    console.log('Formato por turnos explicado:', hasShift ? 'SI' : 'NO');
    console.log('Placeholder correcto:', hasCorrectPlaceholder ? 'SI' : 'NO');
    console.log('='.repeat(50));

    console.log('\n6. Tomando screenshots...');
    
    await page.screenshot({
      path: 'd:/screenshots/break-time-full-page.png',
      fullPage: true
    });
    console.log('   - Screenshot completo guardado');

    const fieldSection = await breakTimeTextarea.locator('..').first();
    await fieldSection.screenshot({
      path: 'd:/screenshots/break-time-field-closeup.png'
    });
    console.log('   - Close-up del campo guardado');

    const allPassed = isVisible && hasNumbered && hasShift && hasCorrectPlaceholder;
    
    console.log('\n' + '='.repeat(50));
    if (allPassed) {
      console.log('RESULTADO FINAL: TODAS LAS VERIFICACIONES PASARON\!');
    } else {
      console.log('RESULTADO FINAL: ALGUNAS VERIFICACIONES FALLARON');
    }
    console.log('='.repeat(50) + '\n');

  } catch (error) {
    console.error('\nERROR:', error.message);
    await page.screenshot({
      path: 'd:/screenshots/error-final-test.png',
      fullPage: true
    });
  } finally {
    console.log('Cerrando navegador en 5 segundos...');
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();
