<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="text-slate-800">
    <nav class="mb-4 text-sm text-slate-600">
      <RouterLink to="/dashboard" class="text-sky-600 hover:underline">Início</RouterLink>
      <span class="mx-2">/</span>
      <span>Ajuda</span>
    </nav>
    <h1 class="mb-2 text-2xl font-semibold text-slate-800">Dúvidas e tutoriais</h1>
    <p class="mb-8 max-w-3xl text-sm text-slate-600">
      Guia rápido para configurar integrações com GitHub, SSH e Docker no TechPanel. Os ícones de informação nos
      formulários apontam para estas secções.
    </p>

    <div class="space-y-10">
      <section id="github-pat" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">GitHub PAT (token no perfil)</h2>
        <p class="mb-3 text-sm leading-relaxed text-slate-600">
          O <strong>Personal Access Token</strong> (PAT) permite ao TechPanel listar repositórios e branches ao
          configurar projetos e pipelines. O token é guardado <strong>encriptado</strong> no servidor.
        </p>
        <ul class="mb-3 list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            Pode ser token <strong>classic</strong> ou <strong>fine-grained</strong>; em ambos os casos precisa de
            permissões que permitam ler repositórios (no TechPanel usamos o escopo <code class="rounded bg-slate-100 px-1 font-mono text-xs">repo</code> como referência).
          </li>
          <li>Se deixar o campo em branco ao guardar o perfil, o token anterior <strong>mantém-se</strong>.</li>
          <li>Use a opção de remover o token se quiser revogar o acesso no painel.</li>
          <li>Nunca partilhe o PAT em chats ou repositórios públicos; trate-o como uma palavra-passe.</li>
        </ul>
        <p class="text-sm text-slate-600">
          Documentação oficial:
          <a
            href="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"
            class="text-sky-600 underline hover:text-sky-800"
            target="_blank"
            rel="noopener noreferrer"
            >Managing personal access tokens</a
          >.
        </p>
      </section>

      <section id="github-repo" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Repositório GitHub (projeto)</h2>
        <p class="mb-3 text-sm leading-relaxed text-slate-600">
          O campo de repositório deve usar o formato <code class="rounded bg-slate-100 px-1 font-mono text-xs">owner/repo</code>
          (ex.: <code class="rounded bg-slate-100 px-1 font-mono text-xs">minha-org/meu-servico</code>). A pesquisa automática
          depende do PAT configurado no perfil. Ao executar uma pipeline, as sugestões de <strong>branch ou tag</strong> usam o
          mesmo repositório do projeto e o mesmo PAT.
        </p>
        <p class="text-sm text-slate-600">
          Se as sugestões falharem, confirme o PAT e os scopes; veja também
          <RouterLink to="/ajuda#github-pat" class="text-sky-600 underline hover:text-sky-800">GitHub PAT</RouterLink>.
        </p>
      </section>

      <section id="tipo-conexao" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Tipo de conexão (servidor)</h2>
        <ul class="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            <strong>SSH</strong>: o TechPanel liga-se a um host remoto por SSH para executar comandos de pipeline (host,
            porta, utilizador e chave privada).
          </li>
          <li>
            <strong>Docker local</strong>: as pipelines correm dentro de um container na máquina onde o backend tem acesso
            ao Docker; não usa host SSH remoto.
          </li>
        </ul>
      </section>

      <section id="ssh-servidor" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Host, porta e utilizador SSH</h2>
        <ul class="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li><strong>Host</strong>: nome DNS ou endereço IP do servidor.</li>
          <li><strong>Porta</strong>: em geral <code class="rounded bg-slate-100 px-1 font-mono text-xs">22</code>, salvo configuração diferente no <code class="rounded bg-slate-100 px-1 font-mono text-xs">sshd</code>.</li>
          <li><strong>Utilizador SSH</strong>: conta no servidor com permissão para os comandos e directórios usados nos ambientes.</li>
          <li>
            O teste de ligação corre no <strong>mesmo sítio que o backend</strong> (servidor ou container), não no teu
            portátil. A chave OpenSSH <code class="rounded bg-slate-100 px-1 font-mono text-xs">ssh-ed25519</code> /
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">BEGIN OPENSSH PRIVATE KEY</code> é suportada;
            confirme host, porta e utilizador (ex.: <code class="rounded bg-slate-100 px-1 font-mono text-xs">root</code>).
          </li>
        </ul>
        <p class="mt-3 text-sm text-slate-600">
          Ajuda GitHub sobre chaves SSH (conceitos gerais):
          <a
            href="https://docs.github.com/en/authentication/connecting-with-ssh"
            class="text-sky-600 underline hover:text-sky-800"
            target="_blank"
            rel="noopener noreferrer"
            >Connecting with SSH</a
          >.
        </p>
      </section>

      <section id="ssh-host-key-policy" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Chave do host SSH (strict vs primeira ligação)</h2>
        <p class="mb-3 text-sm leading-relaxed text-slate-600">
          No formulário do servidor existe a opção <strong>verificação estrita da chave do host</strong>. Isto
          corresponde ao comportamento de <code class="rounded bg-slate-100 px-1 font-mono text-xs">StrictHostKeyChecking</code>
          do OpenSSH na máquina onde corre o <strong>backend</strong> do TechPanel, não no teu portátil.
        </p>
        <ul class="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            <strong>Desligada (omissão)</strong>: na primeira ligação o host é aceite automaticamente (adequado quando o
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">known_hosts</code> do servidor da API ainda não
            conhece o droplet).
          </li>
          <li>
            <strong>Ligada</strong>: só liga se a chave do host já estiver no
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">known_hosts</code> desse ambiente — mais próximo
            de uma política “só hosts já vistos”, com menos risco de aceitar um MITM na primeira vez (desde que o
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">known_hosts</code> esteja correcto).
          </li>
        </ul>
      </section>

      <section id="ssh-chave-privada" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Chave privada (PEM)</h2>
        <p class="mb-3 text-sm leading-relaxed text-slate-600">
          Cole a chave <strong>privada</strong> completa (várias linhas), por exemplo
          <code class="rounded bg-slate-100 px-1 font-mono text-xs">-----BEGIN OPENSSH PRIVATE KEY-----</code> (Ed25519
          ou outros) ou
          <code class="rounded bg-slate-100 px-1 font-mono text-xs">-----BEGIN RSA PRIVATE KEY-----</code>. Não use a
          chave <strong>pública</strong> (<code class="rounded bg-slate-100 px-1 font-mono text-xs">.pub</code>) neste campo.
        </p>
        <ul class="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            No formulário de servidor use o campo <strong>multilinha</strong> para a chave: um
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">input type="password"</code> ou uma única linha
            quebra o formato PEM/OpenSSH e o backend reporta “chave não reconhecida”.
          </li>
          <li>Ao <strong>criar</strong> um servidor, a chave privada é obrigatória.</li>
          <li>Ao <strong>editar</strong>, deixe em branco para manter a chave já guardada no servidor.</li>
        </ul>
      </section>

      <section id="docker-container" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Nome ou ID do container (Docker local)</h2>
        <p class="text-sm leading-relaxed text-slate-600">
          Indique o nome ou o ID tal como aparecem em <code class="rounded bg-slate-100 px-1 font-mono text-xs">docker ps</code>.
          O TechPanel usa esta referência para executar no container certo na máquina local.
        </p>
      </section>

      <section id="pipeline-passos-ssh" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Passos SSH e directório (cd)</h2>
        <p class="mb-3 text-sm leading-relaxed text-slate-600">
          Num <strong>disparo de pipeline</strong>, os passos <code class="rounded bg-slate-100 px-1 font-mono text-xs">ssh_command</code>
          reutilizam a <strong>mesma sessão shell</strong> no servidor (até a execução terminar ou falhar). O directório de
          trabalho do <strong>ambiente</strong> é aplicado com um <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd</code>
          inicial uma vez; depois, um <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd</code> dentro do comando
          de um passo mantém-se para os passos seguintes, desde que não redefina o directório com o campo
          <em>Working dir</em> desse passo.
        </p>
        <ul class="list-disc space-y-2 pl-5 text-sm text-slate-600">
          <li>
            <strong>Exemplo</strong>:
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">ls</code>, depois
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd /tmp</code>, depois
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">ls</code> — o último lista
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">/tmp</code> se não forçar outro
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd</code> no <em>Working dir</em> desse passo.
          </li>
          <li>
            Se o <em>Working dir</em> do passo for <strong>igual</strong> ao directório do ambiente, o motor trata como
            omisso nessa sessão (evita repetir <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd</code> em
            cada passo). Para voltar explicitamente a essa pasta depois de um
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd</code> noutro sítio, use
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd /caminho &amp;&amp; …</code> no texto do comando.
          </li>
          <li>
            <strong>Working dir do passo</strong> (opcional): caminho absoluto; o servidor corre o equivalente a
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">cd [working dir] &amp;&amp; [comando]</code>
            <strong>só nesse passo</strong>, o que repõe o directório antes do comando. Use quando esse passo tiver de
            começar noutra pasta; deixe vazio para continuar onde o shell ficou.
          </li>
          <li>
            <strong>Um passo, várias ordens</strong>: no mesmo campo pode usar
            <code class="rounded bg-slate-100 px-1 font-mono text-xs">ls &amp;&amp; cd subdir &amp;&amp; ls</code>
            (tudo na mesma invocação desse passo).
          </li>
        </ul>
      </section>

      <section id="diretorio-trabalho" class="scroll-mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="mb-3 text-lg font-semibold text-slate-900">Directório de trabalho (ambiente)</h2>
        <p class="text-sm leading-relaxed text-slate-600">
          Caminho absoluto no servidor (ou no contexto do deploy) onde o código do projecto reside e onde os passos da
          pipeline devem correr por omissão. Deve existir e o utilizador SSH precisa de permissão de leitura/execução
          conforme os seus scripts.
        </p>
      </section>
    </div>
  </div>
</template>
