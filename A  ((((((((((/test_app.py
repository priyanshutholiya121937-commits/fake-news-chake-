import unittest
import io
from app import app
from database.database import init_db, save_scan, get_history, get_scan, delete_scan

class TruthCheckAITestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    def test_01_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Detect Fake News', response.data)
        self.assertIn(b'Check News Text', response.data)
        self.assertIn(b'Scan News Photo', response.data)

    def test_02_text_check_page(self):
        response = self.client.get('/text-check')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Check News Text', response.data)

    def test_03_analyze_real_text(self):
        response = self.client.post('/analyze-text', data={
            'headline': 'NASA Discovers New Exoplanet System in Deep Space',
            'article_text': 'Astronomers confirmed the peer-reviewed detection of earth-sized planets orbiting within the habitable zone using spectroscopy.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Likely Real News', response.data)
        self.assertIn(b'Model Confidence', response.data)

    def test_04_analyze_fake_text(self):
        response = self.client.post('/analyze-text', data={
            'headline': 'SHOCKING SECRET: Miracle Lemon Juice Cures All Cancer In 24 Hours BANNED BY DOCTORS',
            'article_text': 'Drinking boiled lemon juice with secret minerals completely vaporizes all terminal diseases overnight! Doctors and big pharma are hiding this truth!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Likely Fake News', response.data)

    def test_05_analyze_empty_text_redirects(self):
        response = self.client.post('/analyze-text', data={
            'headline': '',
            'article_text': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please provide a news headline or article text', response.data)

    def test_06_image_scanner_page(self):
        response = self.client.get('/image-scanner')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Scan News Photo', response.data)
        self.assertIn(b'Use Camera', response.data)
        self.assertIn(b'Upload Image', response.data)

    def test_07_analyze_image_no_input(self):
        response = self.client.post('/analyze-image', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please capture a photo using your camera or upload an image file.', response.data)

    def test_08_history_and_db(self):
        scan_id = save_scan(
            input_type='text',
            original_text='Test News Article for History',
            extracted_text=None,
            prediction='LIKELY REAL',
            confidence=94.5,
            model_used='Test Model'
        )
        self.assertIsNotNone(scan_id)

        # Query history
        records = get_history(search='Test News')
        self.assertTrue(len(records) > 0)

        # View detail
        response = self.client.get(f'/history/{scan_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test News Article', response.data)

        # Delete
        del_resp = self.client.get(f'/history/delete/{scan_id}', follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)

        # Non-existent scan detail redirects to history
        non_existent = self.client.get('/history/999999', follow_redirects=True)
        self.assertEqual(non_existent.status_code, 200)
        self.assertIn(b'Scan record not found.', non_existent.data)

    def test_09_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About TruthCheck AI', response.data)
        self.assertIn(b'TF-IDF', response.data)

if __name__ == '__main__':
    unittest.main()
