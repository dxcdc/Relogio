from django.db import models


class BuzzPost(models.Model):
    """Post original do Buzz"""
    text = models.TextField(verbose_name='Texto')
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE, related_name='buzz_posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-created_at']

    def __str__(self):
        return f"Post de {self.employee} em {self.created_at}"


class BuzzLink(models.Model):
    """Links anexados ao post"""
    post = models.OneToOneField(BuzzPost, on_delete=models.CASCADE, related_name='link')
    link = models.URLField(max_length=500)

    class Meta:
        verbose_name = 'Link'

    def __str__(self):
        return self.link


def buzz_photo_path(instance, filename):
    nome_pasta = "desconhecido"
    if instance.post and instance.post.employee:
        nome_pasta = instance.post.employee.full_name.replace(" ", "_").lower()
    return f'buzz_photos/{nome_pasta}/{filename}'

class BuzzPhoto(models.Model):
    """Fotos do post"""
    post = models.ForeignKey(BuzzPost, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to=buzz_photo_path)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

    def __str__(self):
        return f"Foto de {self.post}"


class BuzzShare(models.Model):
    """Compartilhamento de post"""
    post = models.ForeignKey(BuzzPost, on_delete=models.CASCADE, related_name='shares')
    employee = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE, related_name='buzz_shares'
    )
    type = models.CharField(max_length=20, default='post')
    text = models.TextField(blank=True, null=True, verbose_name='Texto do Compartilhamento')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    num_of_likes = models.IntegerField(default=0)
    num_of_comments = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Compartilhamento'
        verbose_name_plural = 'Compartilhamentos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Share de {self.employee} - Post {self.post.id}"


class BuzzLikeOnShare(models.Model):
    """Curtida em um share"""
    share = models.ForeignKey(BuzzShare, on_delete=models.CASCADE, related_name='likes')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curtida'
        unique_together = ['share', 'employee']

    def __str__(self):
        return f"{self.employee} curtiu {self.share}"


class BuzzComment(models.Model):
    """Comentarios em shares"""
    share = models.ForeignKey(BuzzShare, on_delete=models.CASCADE, related_name='comments')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)
    text = models.TextField(verbose_name='Comentario')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    num_of_likes = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['created_at']

    def __str__(self):
        return f"Comentario de {self.employee}"


class BuzzLikeOnComment(models.Model):
    """Curtida em comentario"""
    comment = models.ForeignKey(BuzzComment, on_delete=models.CASCADE, related_name='likes')
    employee = models.ForeignKey('pim.Employee', on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Curtida no Comentario'
        unique_together = ['comment', 'employee']

    def __str__(self):
        return f"{self.employee} curtiu comentario {self.comment.id}"




class ChangelogPost(models.Model):
    """Nota de atualizacao do sistema publicada pelos administradores."""
    CATEGORY_FEATURE = 'FEATURE'
    CATEGORY_BUGFIX = 'BUGFIX'
    CATEGORY_IMPROVEMENT = 'IMPROVEMENT'
    CATEGORY_SECURITY = 'SECURITY'
    CATEGORY_CHOICES = [
        (CATEGORY_FEATURE, 'Nova Funcionalidade'),
        (CATEGORY_BUGFIX, 'Correcao de Bug'),
        (CATEGORY_IMPROVEMENT, 'Melhoria'),
        (CATEGORY_SECURITY, 'Seguranca'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titulo')
    version = models.CharField(max_length=30, blank=True, verbose_name='Versao/Tag')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_FEATURE, verbose_name='Categoria')
    content = models.TextField(verbose_name='Conteudo')
    pinned = models.BooleanField(default=False, verbose_name='Fixar no topo')
    author = models.ForeignKey('core.OrangeUser', on_delete=models.SET_NULL, null=True, related_name='changelog_posts')
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Nota de Atualizacao'
        verbose_name_plural = 'Notas de Atualizacao'
        ordering = ['-pinned', '-published_at']

    def __str__(self):
        return f"[{self.version}] {self.title}"

    @property
    def category_color(self):
        return {
            'FEATURE': '#10b981',
            'BUGFIX': '#ef4444',
            'IMPROVEMENT': '#3b82f6',
            'SECURITY': '#f59e0b',
        }.get(self.category, '#64748b')

    @property
    def category_bg(self):
        return {
            'FEATURE': '#f0fdf4',
            'BUGFIX': '#fef2f2',
            'IMPROVEMENT': '#eff6ff',
            'SECURITY': '#fffbeb',
        }.get(self.category, '#f8fafc')

    @property
    def category_icon(self):
        return {
            'FEATURE': 'bi-stars',
            'BUGFIX': 'bi-bug',
            'IMPROVEMENT': 'bi-lightning-charge',
            'SECURITY': 'bi-shield-check',
        }.get(self.category, 'bi-info-circle')


def bug_screenshot_path(instance, filename):
    nome_pasta = "desconhecido"
    if instance.reported_by:
        nome_pasta = instance.reported_by.username
    return f'bug_screenshots/{nome_pasta}/{filename}'

class BugReport(models.Model):
    """Relato de bug ou problema reportado por um funcionario."""
    STATUS_OPEN = 'OPEN'
    STATUS_ANALYZING = 'ANALYZING'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_WONTFIX = 'WONTFIX'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Aberto'),
        (STATUS_ANALYZING, 'Em analise'),
        (STATUS_RESOLVED, 'Resolvido'),
        (STATUS_WONTFIX, 'Nao sera corrigido'),
    ]

    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_CRITICAL = 'CRITICAL'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Baixa'),
        (PRIORITY_MEDIUM, 'Media'),
        (PRIORITY_HIGH, 'Alta'),
        (PRIORITY_CRITICAL, 'Critica'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titulo')
    description = models.TextField(verbose_name='Descricao detalhada')
    screenshot = models.ImageField(upload_to=bug_screenshot_path, null=True, blank=True, verbose_name='Captura de tela')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN, verbose_name='Status')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM, verbose_name='Prioridade')
    assigned_to = models.ForeignKey(
        'core.OrangeUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bugs',
        verbose_name='Responsável',
    )
    reported_by = models.ForeignKey('core.OrangeUser', on_delete=models.CASCADE, related_name='bug_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Reporte de Bug'
        verbose_name_plural = 'Reportes de Bug'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

    @property
    def public_comments_count(self):
        """Contagem de comentários visíveis (exclui notas internas)."""
        return self.comments.filter(is_internal=False).count()

    @property
    def status_color(self):
        return {
            'OPEN': '#ef4444',
            'ANALYZING': '#f59e0b',
            'RESOLVED': '#10b981',
            'WONTFIX': '#94a3b8',
        }.get(self.status, '#64748b')

    @property
    def status_bg(self):
        return {
            'OPEN': '#fef2f2',
            'ANALYZING': '#fffbeb',
            'RESOLVED': '#f0fdf4',
            'WONTFIX': '#f8fafc',
        }.get(self.status, '#f8fafc')

    @property
    def priority_color(self):
        return {
            'LOW': '#64748b',
            'MEDIUM': '#3b82f6',
            'HIGH': '#f59e0b',
            'CRITICAL': '#ef4444',
        }.get(self.priority, '#64748b')


class BugReportComment(models.Model):
    """Comentario/resposta a um bug report."""
    bug_report = models.ForeignKey(BugReport, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('core.OrangeUser', on_delete=models.CASCADE, related_name='bug_comments')
    content = models.TextField(verbose_name='Resposta')
    is_internal = models.BooleanField(default=False, verbose_name='Nota interna (so Admin ve)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario de Bug'
        verbose_name_plural = 'Comentarios de Bug'
        ordering = ['created_at']

    def __str__(self):
        return f"Comentario de {self.author} no Bug #{self.bug_report_id}"


def bug_screenshot_item_path(instance, filename):
    nome_pasta = "desconhecido"
    if instance.bug_report and instance.bug_report.reported_by:
        nome_pasta = instance.bug_report.reported_by.username
    return f'bug_screenshots/{nome_pasta}/{filename}'

class BugReportScreenshot(models.Model):
    """Imagem/screenshot anexada a um bug report."""
    bug_report = models.ForeignKey(BugReport, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to=bug_screenshot_item_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Screenshot de Bug'
        verbose_name_plural = 'Screenshots de Bug'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Screenshot do Bug #{self.bug_report_id}"


class ContentReport(models.Model):
    """
    Denúncia de conteúdo inapropriado no Netgram (post ou comentário).
    Exigido pela Apple App Store Guideline 1.2 — User-Generated Content.
    A equipe deve analisar e responder em até 24h.
    """
    CONTENT_TYPE_POST = 'post'
    CONTENT_TYPE_COMMENT = 'comment'
    CONTENT_TYPE_CHOICES = [
        (CONTENT_TYPE_POST, 'Publicação'),
        (CONTENT_TYPE_COMMENT, 'Comentário'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_REVIEWING = 'REVIEWING'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_DISMISSED = 'DISMISSED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_REVIEWING, 'Em análise'),
        (STATUS_RESOLVED, 'Resolvido — conteúdo removido'),
        (STATUS_DISMISSED, 'Arquivado — sem violação'),
    ]

    content_type = models.CharField(
        max_length=10, choices=CONTENT_TYPE_CHOICES, verbose_name='Tipo de Conteúdo'
    )
    content_id = models.IntegerField(verbose_name='ID do Conteúdo')
    reason = models.CharField(max_length=200, verbose_name='Motivo da Denúncia')
    reported_by = models.ForeignKey(
        'pim.Employee', on_delete=models.CASCADE,
        related_name='content_reports', verbose_name='Denunciante'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=STATUS_PENDING, verbose_name='Status'
    )
    moderator_note = models.TextField(
        blank=True, verbose_name='Nota do Moderador'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data da Denúncia')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de Resolução')

    class Meta:
        verbose_name = 'Denúncia de Conteúdo'
        verbose_name_plural = 'Denúncias de Conteúdo'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.get_content_type_display()} #{self.content_id} — {self.reason[:50]}"

