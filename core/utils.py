from django.contrib import messages


def exibir_erros_formulario(request, form):
    """
    Mostra os erros de validacao de um formulario como mensagens na tela.
    """
    for campo, erros in form.errors.items():
        rotulo = form.fields[campo].label if campo in form.fields else None
        for erro in erros:
            messages.error(request, f'{rotulo}: {erro}' if rotulo else erro)
