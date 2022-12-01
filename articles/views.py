from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *
from .models import *
from accounts.models import *
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from accounts.models import *
from django.http import HttpResponseForbidden
from django.db.models import Q, Avg, Count
# Create your views here.
# 게시물 생성
# @login_required(login_url='accounts:login')
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.user = request.user
            article.save()
            return redirect("articles:index")
    else:
        form = ArticleForm()
    context = {
        "form": form,
    }
    return render(request, "articles/create.html", context)


# 게시물 수정
# @login_required(login_url='accounts:login')
def article_update(request, article_pk):
    article = get_object_or_404(Article, pk=article_pk)
    # if request.user != article.author:
    #     message.error(request,'수정권한이 없습니다.')
    #     return redirect('articles:detail',pk=article_pk)
    if request.method == "POST":
        form = ArticleForm(request.POST,request.FILES,  instance=article)
        if form.is_valid():
            article = form.save(commit=False)
            article.save()
            return redirect("articles:index")
    else:
        form = ArticleForm(instance=article)
    context = {"form": form}
    return render(request, "articles/update.html", context)


# def main(request):
#     return render(request, "articles/main.html")

# 게시물 디테일
def article_detail(request, pk):
    # 특정 글을 가져온다.
    article = get_object_or_404(Article, pk=pk)
    user = User.objects.get(pk=request.user.id)
    user_articles = user.article_set.all()
    article_form = ArticleForm()
    comments_form = CommentForm()
    comments = Comment.objects.filter(article_id=pk).order_by("-created_at")
    # template에 객체 전달
    context = {
        "article": article,
        # 역참조 (articles에 포함된 comments data를 전부 불러온다.)
        "articles_form": article_form,
        "comments_form": comments_form,
        "comments": comments,
        "user_articles":user_articles,
        "user":user,
    }
    return render(request, "articles/detail.html", context)


# 게시물 삭제
def article_delete(request, pk):
    if request.user.is_authenticated:
        article = Article.objects.get(pk=pk)
        if request.user == article.user:
            article.delete()
            messages.success(request, "삭제되었습니다.")
    return redirect("articles:index")

# 게시글 좋아요
def like(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.user in article.like_user.all():
        article.like_user.remove(request.user)
        is_liked = False
    else:
        article.like_user.add(request.user)
        is_liked = True
    context = {"isLiked": is_liked, "likeCount": article.like_user.count()}
    return JsonResponse(context)

# 게시물 북마크
def bookmark(request, pk):
    article = get_object_or_404(Article, pk=pk)
    # 만약에 로그인한 유저가 이 글을 북마크를 눌렀다면,
    # if answer.like_users.filter(id=request.user.id).exists():
    if request.user in article.bookmark_user.all():
        # 북마크 삭제하고
        article.bookmark_user.remove(request.user)
        isBookmark = False
    else:
        # 북마크 추가하고
        article.bookmark_user.add(request.user)
        isBookmark = True
    # 상세 페이지로 redirect
    context = {
        "isBookmark": isBookmark,
        "bookMarkCount": article.bookmark_user.count()
    }
    print(context)
    return JsonResponse(context)

# 댓글 생성
def comment_create(request, pk):
    article = get_object_or_404(Article, pk=pk)
    # 위에서 선언된 article의 pk값 저장
    article_pk = article.pk
    # 요청 유저의 pk값 저장
    user = request.user.pk

    comment_form = CommentForm(request.POST)
    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.article = article
        comment.user = request.user
        comment.save()
    # 맨 마지막에 생성된 댓글순으로 comment정보를 저장
    temp = Comment.objects.filter(article_id=pk).order_by("-created_at")
    # 저장된 comment를 담을 리스트
    comment_data = []

    # temp에서 순회하면서 유저의 id, 댓글의 pk, 내용, 생성일자, 닉네임을 각각 comment_data에 담음
    for t in temp:
        t.created_at = t.created_at.strftime("%Y-%m-%d %H:%M")
        comment_data.append(
            {
                "user_id": t.user_id,
                "commentPK": t.pk,
                "content": t.content,
                "created_at": t.created_at,
                "profile_name": t.user.username,
                "count": t.like_user.count()
            }
        )
    # context(data)에 commentData, article의 pk, 요청유저의 pk를 담아서
    data = {"commentData": comment_data, "articlePK": article_pk, "user": user}
    # json으로 리턴
    return JsonResponse(data)
    # return redirect("articles:detail", pk)


# 댓글 삭제
def comment_delete(request, pk, comment_pk):
    # article의 pk값 저장
    article_pk = Article.objects.get(pk=pk).pk
    # 요청 유저의 pk값 저장
    user = request.user.pk
    comment = Comment.objects.get(pk=comment_pk)

    if comment.user == request.user:
        comment.delete()

    # 맨 마지막에 생성된 댓글순으로 comment정보를 저장
    temp = Comment.objects.filter(article_id=pk).order_by("-created_at")
    # 저장된 comment를 담을 리스트
    comment_data = []

    # temp에서 순회하면서 유저의 id, 댓글의 pk, 내용, 생성일자, 닉네임을 각각 comment_data에 담음 
    for t in temp:
        t.created_at = t.created_at.strftime("%Y-%m-%d %H:%M")
        comment_data.append(
            {
                "user_id": t.user_id,
                "commentPK": t.pk,
                "content": t.content,
                "created_at": t.created_at,
                "profile_name": t.user.username,
                "count": t.like_user.count()
            }
        )
    # context(data)에 commentData, article의 pk, 요청유저의 pk를 담아서
    data = {
        "commentData": comment_data,
        "articlePK": article_pk,
        "user": user
    }
    # json으로 리턴
    return JsonResponse(data)






# 댓글 좋아요
def comment_like(request, article_pk, comment_pk):
    temp = Comment.objects.filter(article_id=article_pk)
    for i in temp:
        if i.pk == comment_pk:
            if request.user not in i.like_user.all():
                i.like_user.add(request.user)
                is_like = True
            else:
                i.like_user.remove(request.user)
                is_like = False
            data = {
                "article_pk": article_pk,
                "comment_pk": comment_pk,
                "isLike": is_like,
                'likeCount': i.like_user.count()
            }
            # print(data)
            return JsonResponse(data)

def index(request):
    # 추천순
    sort = request.GET.get('sort','')
    if sort == '1':
        page = request.GET.get("page", "1")
        article = Article.objects.all().annotate(like_cnt=Count('like_user')).order_by('-like_cnt')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 답글많은 순
    elif sort == '2':
        page = request.GET.get("page", "1")
        article = Article.objects.all().annotate(comments=Count('comment')).order_by('-comments')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 내가 쓴 글
    elif sort == '3':
        user = get_user_model().objects.get(pk=request.user.pk)
        page = request.GET.get("page", "1")
        article = user.article_set.all()
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 내가 와드 한 글
    elif sort == '4':
        user = get_user_model().objects.get(pk=request.user.pk)
        page = request.GET.get("page", "1")
        article = user.bookmark_post.all()
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 내가 좋아요 한 글
    elif sort == '5':
        user = get_user_model().objects.get(pk=request.user.pk)
        page = request.GET.get("page", "1")
        article = user.like_post.all()
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 자유
    elif sort == '6':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=1).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 유머
    elif sort == '7':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=2).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 팬아트
    elif sort == '8':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=3).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 유저찾기
    elif sort == '9':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=4).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 유저뉴스
    elif sort == '10':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=5).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 팁과 노하우
    elif sort == '11':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=6).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 기획
    elif sort == '12':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=7).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    # 사건 사고
    elif sort == '13':
        page = request.GET.get("page", "1")
        article = Article.objects.filter(category=8).order_by('-created_at')
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request,"articles/index.html",context)
    else:
        page = request.GET.get("page", "1")
        article = Article.objects.order_by("-created_at")
        paginator = Paginator(article, 20)
        page_obj = paginator.get_page(page)
        context = {"article": page_obj}
        return render(request, "articles/index.html", context)