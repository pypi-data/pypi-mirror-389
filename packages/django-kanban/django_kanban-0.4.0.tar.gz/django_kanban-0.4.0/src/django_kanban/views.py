from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, redirect
from .models import Board, Category, Card
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import BoardForm


def boards(request):
    boards = Board.objects.all()
    return render(request, "kanban/boards.html", {"boards": boards})


def kanban(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    board.update_positions()
    boardForm = None
    categories = board.categories.prefetch_related("cards").all()
    if request.method == "POST":
        boardForm = BoardForm(request.POST, request.FILES, instance=board)
        if "board_id" in request.POST:
            if boardForm.is_valid():
                boardForm.save()
        elif "category_id" in request.POST:
            category_id = request.POST.get("category_id")
            category = Category.objects.get(id=category_id)

            if request.POST.get("category-delete") == "delete":
                category.delete()
            else:
                selected_color = request.POST.get("color")
                category.color = selected_color
                category.save()
        return redirect(request.path)
    else:
        boardForm = BoardForm(instance=board)
    return render(
        request,
        "kanban/kanban.html",
        {
            "board": board,
            "boardForm": boardForm,
            "categories": categories,
        },
    )


def update_card_position(request):
    if request.method == "POST":
        data = json.loads(request.body)
        card_id = data.get("card_id")
        new_category_id = data.get("new_category_id")
        new_position = data.get("new_position")

        try:
            card = Card.objects.get(id=card_id)
            category = Category.objects.get(id=new_category_id)

            card.category = category
            card.update_position(new_position)

            return JsonResponse({"success": True})
        except Card.DoesNotExist:
            return JsonResponse({"success": False, "error": "Card not found"})
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid method"})


def update_category_position(request):
    if request.method == "POST":
        try:
            body = request.body.decode("utf-8")
            data = json.loads(body)

            category_id = data.get("category_id")
            new_position = data.get("new_position")

            if category_id is None or new_position is None:
                return JsonResponse(
                    {"success": False, "error": "Missing category_id or new_position"}
                )

            category = Category.objects.get(id=category_id)
            category.update_position(new_position)

            return JsonResponse({"success": True})

        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid method"})


def add_category(request):
    if request.method == "POST":
        data = json.loads(request.body)
        board_id = data.get("board_id")
        new_category_name = data.get("new_category_name")

        try:
            board = Board.objects.get(id=board_id)
            new_category = Category.objects.create(
                name=new_category_name,
                board=board,
                position=Category.get_highest_category_position() + 1,
            )
            new_category.save()
            return JsonResponse(
                {
                    "success": True,
                    "category_id": new_category.id,
                    "name": new_category.name,
                    "color": new_category.color,
                }
            )
        except Board.DoesNotExist:
            return JsonResponse({"success": False, "error": "Board not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


def add_card(request):
    if request.method == "POST":
        new_card_title = request.POST.get("new_card_title")
        category_id = request.POST.get("category_id")
        image = request.FILES.get("image")

        try:
            category = Category.objects.get(id=category_id)
            new_card = Card.objects.create(
                title=new_card_title,
                category=category,
                position=Card.get_highest_card_position() + 1,
                image=image,  # If null or blank allowed
            )
            return JsonResponse(
                {
                    "success": True,
                    "title": new_card.title,
                    "card_id": new_card.id,
                    "category_id": category.id,
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


def edit_card(request):
    if request.method == "POST":
        data = json.loads(request.body)

        new_card_title = data.get("new_card_title")
        print(new_card_title)
        card_id = data.get("card_id")

        try:
            card = Card.objects.get(id=card_id)
            card.title = new_card_title
            card.save()
            print("CARD TITLE SAVED: ")
            print(card.title)

            return JsonResponse(
                {
                    "success": True,
                }
            )
        except Card.DoesNotExist:
            return JsonResponse({"success": False, "error": "Card not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


def edit_category(request):
    if request.method == "POST":
        data = json.loads(request.body)

        new_category_title = data.get("new_category_title")
        print(new_category_title)
        category_id = data.get("category_id")

        try:
            category = Category.objects.get(id=category_id)
            category.name = new_category_title
            category.save()
            print("CATEGORY TITLE SAVED: ")
            print(category.name)

            return JsonResponse(
                {
                    "success": True,
                }
            )
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "error": "Category not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
