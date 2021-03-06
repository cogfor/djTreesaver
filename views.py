from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.utils import simplejson
from images import Image, Grid
from PIL import Image as ImageCalc
import os
import models

# Serve image at specified size
def serve_image(request, filename, width=None, height=None, root=settings.MEDIA_ROOT):
    width, height = int(width), int(height)
    # Sanitize file path
    filename = filename.replace("/../", "/")
    filename = filename.replace("//", "/")
    while filename.startswith(os.sep):
        filename = filename[1:]
    # open with PIL
    image = Image.open(filename, root=root)
    if width:
        # Scale height
        if not height:
            height = image.scale_height(width)
        resized = image.resize(width, height)
    else:
        resized = image.image
    # Return the response
    response = HttpResponse(mimetype="image/jpg")
    resized.save(response, "JPEG")
    return response
    
# Crops an image to the right size, instead of distorting
def serve_crop(request, filename, width, height, root=settings.MEDIA_ROOT):
    width, height = int(width), int(height)
    filename = filename.replace("/../", "/")
    filename = filename.replace("//", "/")
    while filename.startswith(os.sep):
        filename = filename[1:]
    image = Image.open(filename, root=root)
    image = image.image.transform((width, height), ImageCalc.EXTENT, (0, 0, image.image.size[0], image.image.size[1]))
    # Return the response
    response = HttpResponse(mimetype="image/jpg")
    image.save(response, "JPEG")
    return response

# Serve a solid black image at the specified size
def black(request, width, height):
    width, height = int(width), int(height)
    black = ImageCalc.new("RGB", (width, height))
    # Return the response
    response = HttpResponse(mimetype="image/png")
    black.save(response, "PNG")
    return response

# Redirect to cover of issue    
def view_issue(request, issue):
    issue = models.Issue.objects.get(id=issue)
    return redirect('djTreesaver.views.issue_cover', issue=issue.pk)

# Serve article
def view_article(request, issue, slug):
    issue = models.Issue.objects.get(id=issue)
    article = models.Article.objects.get(slug=slug, issue=issue)
    # Grid selection
    default_grid = settings.TREESAVER.DEFAULT_GRID
    if article.grid:
        default_grid = article.grid.class_id 
    grid = request.GET.get('grid', default_grid)
    # Render
    context = {
        'article' : article,
        'issue' : issue,
        'grid' : grid,
    }
    return render_to_response('article.html', context, context_instance=RequestContext(request))

# Serve issue toc
def issue_toc(request, issue):
    issue = models.Issue.objects.get(id=issue)
    toc = {
        "issueName": issue.title,
        "contents": [{
            "url": article.slug,
            "img": article.toc_image(),
            "publication": issue.publication.name,
            "subject": article.title,
            "title": article.title} for article in issue.articles.all()],
    }
    return HttpResponse(simplejson.dumps(toc))
    

# Serve Cover Image Grid
def issue_cover(request, issue):
    issue = models.Issue.objects.get(id=issue)
    cover_image = issue.cover
    return render_to_response('cover.html', {'cover':cover_image, 'issue':issue}, context_instance=RequestContext(request))

# Treesaver Resources File, containing grids and metadata
def resources(request, issue):
    contents = \
     """{{#contents}}
        <a href="{{url}}">
            <span class="title">{{title}}</span>
            <img src="{{img}}" alt="" />
        </a>
        {{/contents}}"""
    pagenumbers = '<div class="numbering" data-ts-template="position">{{pagenumber}}/{{pagecount}}</div>'
    context = {
        'contents': contents,
        'pagenumbers': pagenumbers,
        'grids' : models.Grid.objects.all(),
        'publication' : models.Issue.objects.get(id=issue).publication,
        'issue' : models.Issue.objects.get(id=issue),
    }
    return render_to_response('resources.html', context, context_instance=RequestContext(request))

    