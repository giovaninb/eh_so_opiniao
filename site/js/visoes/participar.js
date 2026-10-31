import { iniciarFormulario } from "../componentes/formulario.js?v=14";

let formulario = null;

export const participar = {
  titulo: "Participar",
  rotaAtiva: "participar",
  async montar() {
    if (!formulario) formulario = iniciarFormulario();
    formulario.atualizarDisponibilidade();
  },
};
