from modusched.core import BianXieAdapter, ArkAdapter
import pytest


class Test_Bianxie:
    @pytest.fixture
    def bx(self):
        return BianXieAdapter("gemini-2.5-flash-preview-05-20-nothinking")
    
    # @pytest.mark.skip("通过")
    def test_product(self,bx):
        result = bx.product('你好')
        assert isinstance(result,str)
        assert len(result) > 0
        
    async def test_aproduct(self,bx):
        result = await bx.aproduct('你好')
        assert isinstance(result,str)
        assert len(result) > 0

    def test_product_stream(self,bx):
        rus = bx.product_stream("你好")
        for i in rus:
            assert isinstance(i,str)
        
        
    async def test_aproduct_stream(self,bx):
        rus = bx.aproduct_stream("你好")
        async for i in rus:
            assert isinstance(i,str)

    def test_product_image(self,bx):
        bx.model_name = "gemini-2.5-flash-image-preview"
        result = bx.product_image_stream(prompt='绘制两个小孩的照片',
                                  image_path = '')
        for i in result:
            assert isinstance(i,str)
        

class Test_Ark:
    @pytest.fixture
    def ark(self):
        return ArkAdapter("doubao-1-5-pro-256k-250115")

    def test_product(self,ark):
        result = ark.product(prompt='你好')
        assert isinstance(result,str)

    async def test_aproduct(self,ark):
        result = await ark.aproduct(prompt='你好')
        assert isinstance(result,str)
        
    def test_product_stream(self,ark):
        result = ark.product_stream(prompt='你好')
        for chunk in result:
            assert isinstance(chunk,str)


    async def test_aproduct_stream(self,ark):
        result = ark.aproduct_stream(prompt='你好')
        async for chunk in result:
            assert isinstance(chunk,str)


    async def test_tts(self,ark):
        await ark.tts(text = "我是一个小狗狗",
                      filename = "tests/resources/work.wav")


