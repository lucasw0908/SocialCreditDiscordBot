import logging
import random

import discord
from discord.ext import commands

from bot.core import Core
from bot.config import POINT_RADIO, POINT_LIMIT
from bot.utils.embed import EmbedMaker
from bot.utils.emoji import EmojiManager
from bot.utils.button import PageButton


log = logging.getLogger(__name__)

class Score(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        await self.bot.wait_until_ready()
        
        if message.author.bot:
            return
        
        Core.score.add_score(message.author.id, POINT_RADIO)
        Core.user.add_messages(message.author.id)
    
        log.debug(f"Add score to {message.author.name}")
            
            
    @commands.slash_command(name="增加點數", description="增加成員的點數(管理員限定)")
    async def add_score(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="成員"), score: discord.Option(int, name="點數", min_value=-POINT_LIMIT, max_value=POINT_LIMIT)): # type: ignore
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=EmbedMaker(False, "你沒有權限", color="red"))
            return
        
        Core.score.add_score(member.id, score)
        
        await ctx.respond(embed=EmbedMaker(True, description=f"{ctx.author.mention}使用了大人的卡片，{member.mention}的點數獲得了{score}分的{'提升' if score > 0 else '降低'}"))
        
        log.info(f"{ctx.author.name} add {score} score to {member.name}")
        log.debug(f"{ctx.author.name} used add_score command")
        
        
    @commands.slash_command(name="設定點數", description="設定成員的點數(管理員限定)")
    async def set_score(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="成員"), score: discord.Option(int, name="點數", min_value=-POINT_LIMIT, max_value=POINT_LIMIT)): # type: ignore
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=EmbedMaker(False, "你沒有權限", color="red"))
            return
        
        Core.score.set_score(member.id, score)
        
        await ctx.respond(embed=EmbedMaker(True, description=f"{ctx.author.mention}使用了大人的卡片，{member.mention}的點數被設定為{score}分"))
        
        log.info(f"{ctx.author.name} set {member.name}'s score to {score}")
        log.debug(f"{ctx.author.name} used set_score command")
        
        
    @commands.slash_command(name="查詢個人資料", description="查詢成員的點數")
    async def show_score(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="成員", default=None, required=False)): # type: ignore
        
        if member is None:
            member = ctx.author
        
        score = Core.score.get_score(member.id)
        massages = Core.user.get_messages(member.id)
        
        embed = discord.Embed(title=f"個人資料 - {member.name}", color=discord.Color.green())
        embed.add_field(name="", value=f"訊息量: {massages}")
        embed.add_field(name="", value=f"點數: {score}")
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = member.created_at
        
        await ctx.respond(embed=embed)
        
        log.debug(f"Get score of {member.name}")
        log.debug(f"{ctx.author.name} used score command")
        
        
    @commands.slash_command(name="排行榜", description="查詢點數排行榜")
    async def ranklist(self, ctx: discord.ApplicationContext, reverse: discord.Option(bool, name="反向", default=False, required=False)): # type: ignore
        
        limit = 5
        data = Core.score.get_all()
        data = sorted(data, key=lambda x: x["score"], reverse=not reverse)
        list_data = []
        embed = discord.Embed(title="排行榜", color=discord.Color.green())
        
        for i, d in enumerate(data):
            user_id = d["user_id"]
            score = d["score"]
            user = self.bot.get_user(int(user_id))
            if user is None: continue
            list_data.append({
                "name": f"{i+1}. {user.name}",
                "value": f"點數: *{score}*", 
                "inline": False
            })
            
        view = PageButton(ctx=ctx, embed=embed, data=list_data, limit=limit)
            
        await ctx.respond(embed=view.get_embed(), view=view)
        
        log.debug(f"{ctx.author.name} used ranklist command")
        
        
    @commands.slash_command(name="社會信用商店", description="應該...都點的到")
    async def shop(self, ctx: discord.ApplicationContext):
            
        embed = discord.Embed(title="社會信用商店", color=discord.Color.green())
        
        items = Core.item.get_all()
        
        if len(items) == 0:
            embed.add_field(name="", value="***商店空空如也~***")

        for i, item in enumerate(Core.item.get_all()):
            embed.add_field(name=f'{i+1}. {item["name"]}', value=f'價格: *{item["price"]}*\n說明: *{item["description"]}*\n類型: {item["type"]}', inline=False)
        
        await ctx.respond(embed=embed)
        
        log.debug(f"{ctx.author.name} used shop command")
        
        
    @commands.slash_command(name="購買", description="問就是買")
    async def buy(self, ctx: discord.ApplicationContext, item_name: discord.Option(
        str,
        name="商品名稱",  
        autocomplete=lambda x: [discord.OptionChoice(name=item["name"], value=item["name"]) for item in Core.item.get_all()]
        ), # type: ignore
        amount: discord.Option(int, name="數量", default=1, required=False)): # type: ignore
        
        
        for item in Core.item.get_all():
            if item["name"] == item_name:
        
                if Core.score.get_score(ctx.author.id) < item["price"] * amount:
                    await ctx.respond(embed=EmbedMaker(False, "你的點數不足", color="red"))
                    return
                
                if item["type"] == "character":
                    for i in Core.user.get_items(ctx.author.id):
                        if i["name"] == item["name"]:
                            await ctx.respond(embed=EmbedMaker(False, "你已經擁有此物品", color="red"))
                            return
            
                Core.score.add_score(ctx.author.id, -item["price"] * amount)
                Core.user.add_item(ctx.author.id, item, amount=amount)
                
                await ctx.respond(embed=EmbedMaker(True, description=f'你成功購買了{amount}個{item["name"]}'))
                
                log.debug(f'{ctx.author.name} bought {item["name"]}')
                
                return
        
        await ctx.respond(embed=EmbedMaker(False, "找不到此商品", color="red"))
        
        
    @commands.slash_command(name="新增商品", description="新增商品(管理員限定)")
    async def add_item(self, ctx: discord.ApplicationContext, 
                       item_name: discord.Option(str, name="商品名稱", max_length=64), # type: ignore
                       price: discord.Option(str, name="價格", min_length=0, max_length=6), # type: ignore
                       description: discord.Option(str, name="說明", max_length=256)): # type: ignore
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=EmbedMaker(False, "你沒有權限", color="red"))
            return
        
        keywords = ["\n", "\r", "\t", "\u200b", " ", "'", '"', "[", "]", "{", "}", "(", ")", "<", ">", ":", ";", ",", ".", "?", "!", "@", "#", "$", "%", "^", "&", "*", "+", "-", "=", "_", "|", "\\", "/", "`"]
        
        for keyword in keywords:
            if keyword in item_name:
                await ctx.respond(embed=EmbedMaker(False, "商品名稱不能包含特殊字元", color="red"))
                return
            
            if keyword in description:
                await ctx.respond(embed=EmbedMaker(False, "商品說明不能包含特殊字元", color="red"))
                return
            
        if not price.isdigit():
            await ctx.respond(embed=EmbedMaker(False, "價格必須為數字", color="red"))
            return
        
        if Core.item.is_exist(name=item_name):
            await ctx.respond(embed=EmbedMaker(False, "商品已存在", color="red"))
            return
        
        Core.item.add(name=item_name, price=int(price), description=description)
        
        await ctx.respond(embed=EmbedMaker(True, title=item_name, description="新增商品成功"))
        
        log.debug(f'{ctx.author.name} added item {item_name}')
        
        
    @commands.slash_command(name="移除商品", description="移除商品(管理員限定)")
    async def remove_item(self, ctx: discord.ApplicationContext, item_name: discord.Option(
        str,
        name="商品名稱",
        autocomplete=lambda x: [discord.OptionChoice(name=item["name"], value=item["name"]) for item in Core.item.get_all()],
        ), # type: ignore
        removed_from_user: discord.Option(bool, name="從使用者物品移除", default=False, required=False)): # type: ignore
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(embed=EmbedMaker(False, "你沒有權限", color="red"))
            return
        
        if not Core.item.is_exist(name=item_name):
            await ctx.respond(embed=EmbedMaker(False, "找不到此商品", color="red"))
            return
        
        if removed_from_user:
            Core.remove_item_from_user(name=item_name)
        
        Core.item.remove(name=item_name)
        
        await ctx.respond(embed=EmbedMaker(True, description="移除商品成功"))
        
        log.debug(f'{ctx.author.name} removed item {item_name}')
        
        
    @commands.slash_command(name="警告", description="警告社會信用過低的人")
    async def warning(self, ctx: discord.ApplicationContext):

        users = Core.user.get_all()
        
        if len(users) == 0:
            member = ctx.author
        else:
            member = self.bot.get_user(random.choice([int(user["user_id"]) for user in users if user["score"] < 100])) or ctx.author
        
        embed = discord.Embed(title="警告", color=discord.Color.red())
        embed.add_field(name="", value=f"{member.mention} 您的社會信用點數過低!!! \n目前點數為: {Core.score.get_score(member.id)} \n建議多發言以提升您的社會信用點數")
        
        await ctx.respond(embed=embed)
        
        log.debug(f'{ctx.author.name} warned {member.name}')
        
        
    @commands.slash_command(name="shiroko", description="嘿嘿嘿")
    async def shiroko(self, ctx: discord.ApplicationContext):
        
        success = random.choice([True, False])
        if success: value = random.randint(1, 114)
        else: value = random.randint(-114, -1)
        
        Core.score.add_score(ctx.author.id, value)
        
        embed = discord.Embed(title="搶銀行囉", color=discord.Color.green() if success else discord.Color.red())
        embed.set_image(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsPASopxuiwUm2auuA8WKKjFyB7Yy13oVMjQ&s")
        embed.add_field(name="成果", value=f'{"成功搶到了" if success else "被抓到了，因此被罰了"}{abs(value)}點社會信用點數')
        
        await ctx.respond(embed=embed)
        
        log.debug(f'{ctx.author.name} used shiroko command')
        
        
    @commands.slash_command(name="轉帳", description="轉帳程序需酌收5%手續費")
    async def transfer(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="成員"), score: discord.Option(int, name="點數", min_value=1)): # type: ignore
        
        if Core.score.get_score(ctx.author.id) < score:
            await ctx.respond(embed=EmbedMaker(False, "你的點數不足", color="red"))
            return
        
        Core.score.add_score(ctx.author.id, -score)
        Core.score.add_score(member.id, int(round(score * 0.95)))
        
        embed = discord.Embed(title=EmojiManager("轉帳成功:animation_yes:"), color=discord.Color.green())
        embed.add_field(name="持有者", value=ctx.author.mention, inline=False)
        embed.add_field(name="對象", value=member.mention, inline=False)
        embed.add_field(name="金額", value=f"{score}$", inline=False)
        embed.add_field(name="手續費", value=f"{round(score * 0.05)}$", inline=False) 
        
        await ctx.respond(embed=embed)
        
        log.debug(f'{ctx.author.name} transfered {score} score to {member.name}')
        
        
    @commands.slash_command(name="使用物品", description="使用獲得的物品")
    async def use_item(self, ctx: discord.ApplicationContext, item_name: discord.Option(
        str,
        name="物品名稱",
        autocomplete=lambda x: [discord.OptionChoice(name=item["name"], value=item["name"]) for item in Core.item.get_all()],
        ), # type: ignore
        amount: discord.Option(int, name="數量", default=1, required=False)): # type: ignore
        
        user_items = Core.user.get_items(ctx.author.id)
        if len(user_items) == 0:
            await ctx.respond(embed=EmbedMaker(False, "你的物品欄是空的", color="red"))
            return None
        
        for item in user_items:
            if item["name"] == item_name and item["count"] >= amount:
                
                match item["name"]:
                    
                    case "林檎": 
                        await Core.item.use_ringo(Core, ctx, amount=amount)
                        
                    case _:
                        await ctx.respond(embed=EmbedMaker(False, description=f"此物品無法使用"))
                        return None
                    
                Core.user.add_item(ctx.author.id, Core.item.get(name=item["name"]), -1)
                # await ctx.respond(embed=EmbedMaker(True, description=f'你使用了{item_name}'))
                
                log.debug(f'{ctx.author.name} used {item_name}')
                
                return None
            
        await ctx.respond(embed=EmbedMaker(False, "你的物品數量不足"))
    
    
    @commands.slash_command(name="物品欄", description="查詢擁有的物品")
    async def item_list(self, ctx: discord.ApplicationContext, member: discord.Option(discord.Member, name="成員", default=None, required=False)): # type: ignore
        
        if member is None:
            member = ctx.author
        
        items = Core.user.get_items(member.id)
        embed = discord.Embed(title=f"{member.name}的物品欄", color=discord.Color.green())
        
        if len(items) == 0:
            embed.add_field(name="", value="***物品欄空空如也~***")
        
        for i, item in enumerate(items):
            embed.add_field(name=f'{i+1}. {item["name"]}', value=f'說明: *{item["description"]}*\n數量: {item["count"]}', inline=False)
        
        await ctx.respond(embed=embed)
        
        log.debug(f'{ctx.author.name} get item list of {member.name}')
        


def setup(bot: commands.Bot):
    bot.add_cog(Score(bot))