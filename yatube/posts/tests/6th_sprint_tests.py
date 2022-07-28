import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from posts.models import Group, Post
from django.contrib.auth import get_user_model


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PictureWorksTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='pushkin')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        # cls.form = PostForm()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='from setup',
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_picture_creates_by_form(self):
        b4_test = Post.objects.count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        # Отправляем POST-запрос
        response = self.auth_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), b4_test + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               args=[self.user.username]))

    def test_context_gets_picture(self):
        exp_pic_name = 'posts/small.gif'
        reverses = [
            reverse('posts:index'),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:group_list', args=[self.group.slug]),
        ]
        for cur_reverse in reverses:
            with self.subTest(cur_reverse=cur_reverse):
                response = self.auth_client.get(cur_reverse)
                pic_name = self.get_pic_name(response)
                self.assertEqual(pic_name, exp_pic_name)

        p_d_reverse = reverse('posts:post_detail', args=[self.post.id])
        p_d_response = self.auth_client.get(p_d_reverse)
        post_pic_name = p_d_response.context['post'].image.name
        self.assertEqual(post_pic_name, exp_pic_name)

    def get_pic_name(self, r):
        return r.context['page_obj'][0].image.name
